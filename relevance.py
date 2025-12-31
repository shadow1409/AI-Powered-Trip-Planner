# -*- coding: utf-8 -*-
# relevance.py
# -------------------------------------------------
# Purpose:
# Compute relevance scores between user interests
# and filtered events, with tourism bias
# -------------------------------------------------

import json
import pandas as pd

# -------------------------------------------------
# CONFIG
# -------------------------------------------------

FILTERED_CSV = "filtered.csv"
INPUT_JSON = "input.json"
OUTPUT_CSV = "final.csv"

TOURISM_BIAS = 0.4

# Categories (MUST MATCH DATASET & input.json)
CATEGORIES = [
    "religious_spiritual","literature_poetry","art_exhibition",
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

TOURISM_CATEGORIES = {
    "seaside_beach","cultural_heritage","heritage_walk",
    "sunset_view","sunrise_view","mountain_climbing",
    "boating_cruise","lake_activity","island_experience",
    "river_ghat","desert_experience","snow_activity",
    "wildlife_safari","forest_trail"
}

# -------------------------------------------------
# LOAD INPUTS
# -------------------------------------------------

with open(INPUT_JSON, "r", encoding="utf-8") as f:
    user_vector = json.load(f)

df = pd.read_csv(FILTERED_CSV)

# -------------------------------------------------
# SAFETY CHECKS
# -------------------------------------------------

required_cols = {"event_name", "city", "state", "start_date", "end_date"}
missing = required_cols - set(df.columns)
if missing:
    raise ValueError(f"filtered.csv missing required columns: {missing}")

# Ensure all category columns exist
for cat in CATEGORIES:
    if cat not in df.columns:
        df[cat] = 0

# -------------------------------------------------
# RELEVANCE SCORING FUNCTION
# -------------------------------------------------

def compute_relevance(event_row: pd.Series) -> float:
    """
    Weighted similarity score between user vector
    and event category vector, with tourism bias.
    """

    score = 0.0
    weight_sum = 0.0

    for cat in CATEGORIES:
        user_weight = float(user_vector.get(cat, 0.0))
        event_value = float(event_row.get(cat, 0))

        if event_value > 0 and user_weight > 0:
            score += user_weight * event_value
            weight_sum += user_weight

    if weight_sum > 0:
        score = score / weight_sum
    else:
        score = 0.0

    # Tourism bias
    if any(event_row.get(cat, 0) == 1 for cat in TOURISM_CATEGORIES):
        score += TOURISM_BIAS

    # Clamp score to [0, 1]
    score = max(0.0, min(1.0, score))

    return round(score, 4)

# -------------------------------------------------
# APPLY SCORING
# -------------------------------------------------

df["relevance_score"] = df.apply(compute_relevance, axis=1)

# -------------------------------------------------
# FINAL OUTPUT
# -------------------------------------------------

final_df = df[
    ["event_name","city","state","relevance_score","start_date","end_date"]
].sort_values(
    by="relevance_score",
    ascending=False
).reset_index(drop=True)

final_df.to_csv(OUTPUT_CSV, index=False)

print(f"Final ranked events saved to {OUTPUT_CSV}")
print(final_df.head(10))
