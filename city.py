# city.py
# -------------------------------------------------
# Purpose:
# Filter events by selected cities and trip duration
# Accepts inputs via CLI (for Streamlit orchestration)
# -------------------------------------------------

import pandas as pd
import argparse

# -------------------------------------------------
# CONFIG
# -------------------------------------------------

CSV_FILE = "india_events_2000_tourism_2026_latlon.csv"
OUTPUT_CSV = "filtered.csv"
DATE_FMT = "%Y-%m-%d"

# -------------------------------------------------
# CORE FUNCTION
# -------------------------------------------------

def filter_events_by_city_and_date(
    cities: list[str],
    trip_start_date: str,
    trip_end_date: str
) -> pd.DataFrame:

    df = pd.read_csv(CSV_FILE)

    # --- FIX 1: Normalize city column ---
    df["city"] = df["city"].astype(str).str.strip()
    df["city_norm"] = df["city"].str.lower()

    # --- FIX 2: Normalize input cities ---
    cities_norm = [c.strip().lower() for c in cities if c.strip()]

    # Parse dates (ISO safe)
    df["start_date"] = pd.to_datetime(
        df["start_date"], format=DATE_FMT, errors="coerce"
    )
    df["end_date"] = pd.to_datetime(
        df["end_date"], format=DATE_FMT, errors="coerce"
    )

    df = df.dropna(subset=["start_date", "end_date"])

    trip_start = pd.to_datetime(trip_start_date, format=DATE_FMT)
    trip_end = pd.to_datetime(trip_end_date, format=DATE_FMT)

    # --- FIX 3: Correct city filtering ---
    df = df[df["city_norm"].isin(cities_norm)]

    # Date overlap filter
    df = df[
        (df["start_date"] <= trip_end) &
        (df["end_date"] >= trip_start)
    ]

    # Cleanup helper column
    df = df.drop(columns=["city_norm"])

    # Deterministic ordering
    df = df.sort_values(
        by=["city", "start_date", "start_time"],
        na_position="last"
    ).reset_index(drop=True)

    return df

# -------------------------------------------------
# CLI ENTRY POINT
# -------------------------------------------------

if __name__ == "__main__":

    parser = argparse.ArgumentParser()
    parser.add_argument("--cities", required=True)
    parser.add_argument("--start", required=True)
    parser.add_argument("--end", required=True)

    args = parser.parse_args()

    cities = args.cities.split(",")

    filtered_df = filter_events_by_city_and_date(
        cities=cities,
        trip_start_date=args.start,
        trip_end_date=args.end
    )

    filtered_df.to_csv(OUTPUT_CSV, index=False)

    print(f"Filtered events saved to {OUTPUT_CSV}")
    print(f"Total events found: {len(filtered_df)}")
    print(f"Cities found: {sorted(filtered_df['city'].unique())}")
