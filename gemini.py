# gemini.py
# -------------------------------------------------
# Purpose:
# Convert user interest text into structured
# interest metadata using Gemini
# Accepts input via CLI (for Streamlit orchestration)
# -------------------------------------------------

import os
import json
import argparse
from google import genai
from google.genai import types

# -------------------------------------------------
# CATEGORY LIST (MUST MATCH DATASET)
# -------------------------------------------------

CATEGORIES = [
    "religious_spiritual","cultural_heritage","literature_poetry","art_exhibition",
    "dance_performing","film_media","comedy_standup","music_classical_folk",
    "music_contemporary","nightlife","celebrity_event","food_culinary",
    "fashion_lifestyle","wellness_mental","nature_outdoor","education_workshop",
    "technology_innovation","hackathon_coding","startup_business",
    "academic_conference","roadshow","airshow_aviation","auto_motor",
    "gaming_esports","science_space","sports_fitness","adventure_extreme",
    "community_social","government_public","trade_expo",
    "sunset_view","sunrise_view","seaside_beach","mountain_climbing",
    "boating_cruise","wildlife_safari","desert_experience","snow_activity",
    "heritage_walk","street_festival","local_fair","lake_activity",
    "forest_trail","island_experience","river_ghat"
]

# -------------------------------------------------
# PROMPT TEMPLATE
# -------------------------------------------------

PROMPT_TEMPLATE = """
You are an information extraction system.

Task:
Convert the user's interest description into a JSON object.

Rules:
- Output ONLY valid JSON.
- Include ALL categories listed below.
- Values must be floats between 0.0 and 1.0.
- 1.0 = strong interest
- 0.0 = no interest
- Do not add explanations.
- Do not add extra keys.

Categories:
{categories}

User input:
"{user_input}"
"""

# -------------------------------------------------
# GEMINI SETUP
# -------------------------------------------------

if "GEMINI_API_KEY" not in os.environ:
    raise EnvironmentError("GEMINI_API_KEY not set in environment variables.")

client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])

MODEL_NAME = "gemini-2.5-flash-lite"

# -------------------------------------------------
# CORE FUNCTION
# -------------------------------------------------

def extract_interest_metadata(user_text: str) -> dict:
    prompt = PROMPT_TEMPLATE.format(
        categories=", ".join(CATEGORIES),
        user_input=user_text
    )

    response = client.models.generate_content(
        model=MODEL_NAME,
        contents=prompt,
        config=types.GenerateContentConfig(
            temperature=0.0,
            response_mime_type="application/json"
        )
    )

    try:
        metadata = json.loads(response.text)
    except json.JSONDecodeError:
        raise ValueError("Gemini did not return valid JSON.")

    cleaned = {}
    for cat in CATEGORIES:
        try:
            val = float(metadata.get(cat, 0.0))
        except (TypeError, ValueError):
            val = 0.0
        cleaned[cat] = max(0.0, min(1.0, val))

    return cleaned

# -------------------------------------------------
# CLI ENTRY POINT (FOR STREAMLIT)
# -------------------------------------------------

if __name__ == "__main__":

    parser = argparse.ArgumentParser(
        description="Extract interest metadata using Gemini"
    )

    parser.add_argument(
        "--interest",
        required=True,
        help="User interest description text"
    )

    args = parser.parse_args()

    interest_text = args.interest.strip()

    if not interest_text:
        raise ValueError("Interest text cannot be empty.")

    metadata = extract_interest_metadata(interest_text)

    with open("input.json", "w", encoding="utf-8") as f:
        json.dump(metadata, f, indent=2)

    print("Interest metadata saved to input.json")
