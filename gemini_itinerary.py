# -*- coding: utf-8 -*-
# gemini_itinerary.py
# -------------------------------------------------
# Purpose:
# Convert plan.json into a UI-friendly structured
# itinerary using Gemini (presentation-only step)
# Streamlit + deployment safe
# -------------------------------------------------

import os
import json
import time
from google import genai
from google.genai import types
from google.genai.errors import ClientError

# -------------------------------------------------
# CONFIG
# -------------------------------------------------

INPUT_PLAN = "plan.json"
OUTPUT_ITINERARY = "itinerary.json"
MODEL_NAME = "gemini-2.5-flash-lite"

# -------------------------------------------------
# LOAD API KEYS (MULTI-KEY SAFE)
# -------------------------------------------------

def load_api_keys():
    """
    Supports:
    GEMINI_API_KEY=key
    OR
    GEMINI_API_KEYS=key1,key2,key3
    """
    if "GEMINI_API_KEYS" in os.environ:
        return [k.strip() for k in os.environ["GEMINI_API_KEYS"].split(",") if k.strip()]
    if "GEMINI_API_KEY" in os.environ:
        return [os.environ["GEMINI_API_KEY"].strip()]
    return []

API_KEYS = load_api_keys()

if not API_KEYS:
    raise EnvironmentError("No Gemini API keys found in environment variables.")

# -------------------------------------------------
# LOAD PLAN.JSON (SOURCE OF TRUTH)
# -------------------------------------------------

with open(INPUT_PLAN, "r", encoding="utf-8") as f:
    plan = json.load(f)

# -------------------------------------------------
# STRICT PROMPT
# -------------------------------------------------

prompt = f"""
You are a formatting and explanation system.

You are given a structured trip plan in JSON.
This JSON is the SINGLE SOURCE OF TRUTH.

=====================
ABSOLUTE RULES
=====================
- DO NOT remove any cities.
- DO NOT remove any events.
- DO NOT summarize, merge, or skip events.
- DO NOT change dates, scores, or ordering.
- DO NOT invent activities, cities, or facts.
- DO NOT recompute relevance.
- DO NOT add or remove keys except where explicitly instructed.
- ONLY add natural-language explanations.

If a city contains ONLY flexible exploration activities,
it MUST still appear fully in the output.

=====================
YOUR TASK
=====================
1. Wrap the input JSON into the OUTPUT JSON SCHEMA below.
2. Preserve ALL cities and ALL events exactly as provided.
3. Add the following explanations:

For EACH CITY:
- "city_overview":
  A neutral 1–2 sentence factual overview of the city.
- "city_reason":
  1–2 sentences explaining why this city fits the user's interests,
  based ONLY on:
    • the types of events present
    • their qualitative relevance levels

For EACH EVENT:
- "description":
  One sentence explaining what the activity involves.
- "relevance_note":
  One short sentence explaining why this activity aligns
  with the user's interests.

4. Convert all events into UI-friendly "activities".

=====================
IMPORTANT CONSTRAINTS
=====================
- You MAY refer to relevance qualitatively
  (e.g., “highly relevant”, “moderately aligned”).
- You MUST NOT mention numeric relevance values.
- You MUST NOT compare cities with each other.
- You MUST NOT suggest skipping or removing any city.
- Flexible activities such as "Exploring <City>" are
  VALID and IMPORTANT activities.

=====================
OUTPUT JSON SCHEMA
(MUST MATCH EXACTLY)
=====================

{{
  "trip_summary": {{
    "start_date": "...",
    "end_date": "...",
    "cities_covered": ["City1", "City2"]
  }},
  "itinerary": [
    {{
      "city": "...",
      "visit_window": {{
        "start_date": "...",
        "end_date": "..."
      }},
      "city_overview": "...",
      "city_reason": "...",
      "activities": [
        {{
          "title": "...",
          "type": "fixed_event | flexible_activity",
          "date_info": "...",
          "description": "...",
          "relevance_note": "..."
        }}
      ]
    }}
  ]
}}

=====================
FORMATTING GUIDELINES
=====================
- Use plan.trip_start and plan.trip_end for trip_summary.
- cities_covered MUST list cities in the SAME ORDER as input.
- Fixed events:
  date_info = "YYYY-MM-DD" or "YYYY-MM-DD → YYYY-MM-DD"
- Flexible activities:
  date_info = "Any free day in <city>"

=====================
INPUT JSON
=====================
{json.dumps(plan, indent=2)}
"""

# -------------------------------------------------
# GEMINI CALL WITH FALLBACK
# -------------------------------------------------

def generate_itinerary():
    last_error = None

    for api_key in API_KEYS:
        try:
            client = genai.Client(api_key=api_key)

            response = client.models.generate_content(
                model=MODEL_NAME,
                contents=prompt,
                config=types.GenerateContentConfig(
                    temperature=0.0,
                    response_mime_type="application/json"
                )
            )

            raw = response.text.strip()

            if raw.startswith("```"):
                raw = raw.split("```")[1].strip()

            return json.loads(raw)

        except (ClientError, json.JSONDecodeError) as e:
            last_error = e
            time.sleep(1)
            continue

    # -------------------------------------------------
    # FAIL-SAFE FALLBACK (NO GEMINI)
    # -------------------------------------------------

    print("⚠️ Gemini unavailable. Falling back to minimal itinerary.")

    return {
        "trip_summary": {
            "start_date": plan["trip_start"],
            "end_date": plan["trip_end"],
            "cities_covered": [c["city"] for c in plan["cities"]]
        },
        "itinerary": [
            {
                "city": c["city"],
                "visit_window": {
                    "start_date": c["city_start_date"],
                    "end_date": c["city_end_date"]
                },
                "city_overview": "This city is included in your trip itinerary.",
                "city_reason": "This city contains events aligned with your selected interests.",
                "activities": [
                    {
                        "title": e["name"],
                        "type": e["type"],
                        "date_info": (
                            f'{e.get("start_date")} → {e.get("end_date")}'
                            if e["type"] == "fixed_event"
                            else f'Any free day in {c["city"]} (1 day)'
                        ),
                        "description": "Planned activity during your visit.",
                        "relevance_note": "This activity aligns with your interests."
                    }
                    for e in c["events"]
                ]
            }
            for c in plan["cities"]
        ]
    }

# -------------------------------------------------
# SAVE OUTPUT
# -------------------------------------------------

itinerary = generate_itinerary()

with open(OUTPUT_ITINERARY, "w", encoding="utf-8") as f:
    json.dump(itinerary, f, indent=2)

print(f"Structured itinerary saved to {OUTPUT_ITINERARY}")
