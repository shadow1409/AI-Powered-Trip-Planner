# gemini_itinerary.py
# -------------------------------------------------
# Purpose:
# Convert plan.json into a UI-friendly structured
# itinerary using Gemini (presentation-only step)
# -------------------------------------------------

import os
import json
from google import genai
from google.genai import types

# -------------------------------------------------
# CONFIG
# -------------------------------------------------

INPUT_PLAN = "plan.json"
OUTPUT_ITINERARY = "itinerary.json"
MODEL_NAME = "gemini-2.5-flash-lite"

# -------------------------------------------------
# ENVIRONMENT CHECK
# -------------------------------------------------

if "GEMINI_API_KEY" not in os.environ:
    raise EnvironmentError("GEMINI_API_KEY not set in environment variables.")

client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])

# -------------------------------------------------
# LOAD PLAN.JSON (SOURCE OF TRUTH)
# -------------------------------------------------

with open(INPUT_PLAN, "r", encoding="utf-8") as f:
    plan = json.load(f)

# -------------------------------------------------
# STRICT PROMPT (NO DROPPING / NO REORDERING)
# -------------------------------------------------

prompt = f"""
You are a formatting and explanation system.

You are given a structured trip plan in JSON.
This JSON is the SINGLE SOURCE OF TRUTH.

ABSOLUTE RULES (DO NOT VIOLATE):
- DO NOT remove any cities.
- DO NOT remove any events.
- DO NOT summarize, merge, or skip events.
- DO NOT change dates, scores, or order.
- DO NOT invent data.
- DO NOT recompute relevance.
- DO NOT add or remove keys except where explicitly asked.
- ONLY add natural-language explanations.

Your task:
1. Wrap the input into the OUTPUT JSON SCHEMA below.
2. Preserve ALL cities and ALL events exactly.
3. Add:
   - "city_overview": 1–2 sentence factual overview of the city.
   - "city_reason": 1–2 sentences explaining *why this city fits the user's interests*,
     based ONLY on the relevance scores and types of events present.
   - "description": 1 sentence per event explaining what it is.
   - "relevance_note": 1 short sentence per event explaining
     why this event is relevant given the user's interests.
4. Convert events into UI-friendly "activities" entries.

IMPORTANT:
- You may REFER to relevance_score qualitatively (e.g., “high relevance”, “moderate relevance”).
- You may NOT mention numeric values directly.
- You may NOT compare cities against each other.
- You may NOT recommend skipping any city.

OUTPUT JSON SCHEMA (MUST MATCH EXACTLY):

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

Guidelines:
- Use plan.trip_start and plan.trip_end for trip_summary.
- cities_covered must list cities in order.
- For fixed events:
  date_info = "YYYY-MM-DD" or "YYYY-MM-DD → YYYY-MM-DD"
- For flexible activities:
  date_info = "Any free day in <city> (1 day)"

INPUT JSON:
{json.dumps(plan, indent=2)}
"""


# -------------------------------------------------
# GEMINI CALL
# -------------------------------------------------

response = client.models.generate_content(
    model=MODEL_NAME,
    contents=prompt,
    config=types.GenerateContentConfig(
        temperature=0.0,
        response_mime_type="application/json"
    )
)


raw = response.text.strip()

# Defensive cleanup (Gemini safety)
if raw.startswith("```"):
    raw = raw.split("```")[1].strip()

# -------------------------------------------------
# PARSE & SAVE OUTPUT
# -------------------------------------------------

try:
    itinerary = json.loads(raw)
except json.JSONDecodeError as e:
    raise ValueError(
        "Gemini did not return valid JSON. "
        "This should not happen with strict prompting."
    ) from e

with open(OUTPUT_ITINERARY, "w", encoding="utf-8") as f:
    json.dump(itinerary, f, indent=2)

print(f"Structured itinerary saved to {OUTPUT_ITINERARY}")
