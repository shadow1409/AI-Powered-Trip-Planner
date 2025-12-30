# -*- coding: utf-8 -*-
# planner.py
# -------------------------------------------------
# Purpose:
# Convert final.csv into a structured planning JSON
# ordered strictly by time (city order),
# with events sorted by relevance within each city.
# plan.json is the SINGLE SOURCE OF TRUTH.
# -------------------------------------------------

import pandas as pd
import json
import argparse
from datetime import datetime

# -------------------------------------------------
# CONFIG
# -------------------------------------------------

FINAL_CSV = "final.csv"
OUTPUT_JSON = "plan.json"
DATE_FMT = "%Y-%m-%d"

FLEXIBLE_KEYWORDS = ["explore", "attractions"]

W_RELEVANCE = 0.5
W_DENSITY = 0.5

# -------------------------------------------------
# ARGUMENTS
# -------------------------------------------------

parser = argparse.ArgumentParser(description="Build structured trip plan JSON")
parser.add_argument("--start", required=True, help="Trip start date (YYYY-MM-DD)")
parser.add_argument("--end", required=True, help="Trip end date (YYYY-MM-DD)")
args = parser.parse_args()

trip_start = datetime.strptime(args.start, DATE_FMT)
trip_end = datetime.strptime(args.end, DATE_FMT)

# -------------------------------------------------
# HELPERS
# -------------------------------------------------

def is_flexible_event(event_name: str) -> bool:
    name = event_name.lower()
    return all(k in name for k in FLEXIBLE_KEYWORDS)


def event_duration(start, end):
    return (end - start).days + 1


def average_gap_days(events):
    if len(events) <= 1:
        return 0.0

    gaps = []
    for i in range(len(events) - 1):
        gap = (events[i + 1]["start"] - events[i]["end"]).days - 1
        gaps.append(max(0, gap))

    return sum(gaps) / len(gaps)

# -------------------------------------------------
# LOAD DATA
# -------------------------------------------------

df = pd.read_csv(FINAL_CSV)

required_cols = {"event_name", "city", "start_date", "end_date", "relevance_score"}
missing = required_cols - set(df.columns)
if missing:
    raise ValueError(f"final.csv is missing required columns: {missing}")

df["start_date"] = pd.to_datetime(df["start_date"], format=DATE_FMT, errors="coerce")
df["end_date"] = pd.to_datetime(df["end_date"], format=DATE_FMT, errors="coerce")

df = df.dropna(subset=["start_date", "end_date", "city"])

# Normalize city names
df["city"] = df["city"].astype(str).str.strip()

# -------------------------------------------------
# BUILD PLAN.JSON
# -------------------------------------------------

plan = {
    "trip_start": args.start,
    "trip_end": args.end,
    "cities": []
}

for city, city_df in df.groupby("city", sort=False):

    fixed_events = []
    flexible_events = []

    for _, row in city_df.iterrows():

        if is_flexible_event(row["event_name"]):
            flexible_events.append({
                "name": row["event_name"],
                "type": "flexible_activity",
                "duration_days": 1,
                "relevance": round(float(row["relevance_score"]), 4)
            })
        else:
            fixed_events.append({
                "name": row["event_name"],
                "type": "fixed_event",
                "start": row["start_date"],
                "end": row["end_date"],
                "duration_days": event_duration(row["start_date"], row["end_date"]),
                "relevance": round(float(row["relevance_score"]), 4)
            })

    # Sort fixed events by time (for visit window)
    fixed_events.sort(key=lambda e: e["start"])

    if fixed_events:
        city_start_date = fixed_events[0]["start"]
        city_end_date = fixed_events[-1]["end"]
    else:
        city_start_date = trip_start
        city_end_date = trip_end

    # -----------------------------
    # CITY SCORE (METADATA ONLY)
    # -----------------------------

    if fixed_events:
        mean_relevance = sum(e["relevance"] for e in fixed_events) / len(fixed_events)
        avg_gap = average_gap_days(fixed_events)
        density_score = 1 / (1 + avg_gap)
    else:
        mean_relevance = 0.0
        density_score = 0.0

    city_score = W_RELEVANCE * mean_relevance + W_DENSITY * density_score

    # -----------------------------
    # OUTPUT EVENTS (SORTED BY RELEVANCE)
    # -----------------------------

    output_events = []

    for e in fixed_events:
        output_events.append({
            "name": e["name"],
            "type": "fixed_event",
            "start_date": e["start"].strftime(DATE_FMT),
            "end_date": e["end"].strftime(DATE_FMT),
            "duration_days": e["duration_days"],
            "relevance": e["relevance"]
        })

    output_events.extend(flexible_events)

    # 🔹 Sort ALL events by relevance (descending)
    output_events.sort(key=lambda x: x["relevance"], reverse=True)

    plan["cities"].append({
        "city": city,
        "city_score": round(city_score, 4),
        "city_start_date": city_start_date.strftime(DATE_FMT),
        "city_end_date": city_end_date.strftime(DATE_FMT),
        "events": output_events
    })

# -------------------------------------------------
# SORT CITIES STRICTLY BY TIME
# -------------------------------------------------

plan["cities"].sort(key=lambda c: c["city_start_date"])

# -------------------------------------------------
# SAVE plan.json
# -------------------------------------------------

with open(OUTPUT_JSON, "w", encoding="utf-8") as f:
    json.dump(plan, f, indent=2)

print(f"Planning JSON saved to {OUTPUT_JSON}")
