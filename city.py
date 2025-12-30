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

# -------------------------------------------------
# CORE FUNCTION
# -------------------------------------------------

def filter_events_by_city_and_date(
    cities: list[str],
    trip_start_date: str,
    trip_end_date: str
) -> pd.DataFrame:
    """
    Filters events that:
    1. Belong to the given cities
    2. Overlap with the trip duration
    """

    df = pd.read_csv(CSV_FILE)

    # Robust date parsing
    df["start_date"] = pd.to_datetime(
        df["start_date"], errors="coerce", dayfirst=True
    )
    df["end_date"] = pd.to_datetime(
        df["end_date"], errors="coerce", dayfirst=True
    )

    # Drop invalid dates
    df = df.dropna(subset=["start_date", "end_date"])

    trip_start = pd.to_datetime(trip_start_date)
    trip_end = pd.to_datetime(trip_end_date)

    # Filter by city
    df = df[df["city"].isin(cities)]

    # Filter by date overlap
    df = df[
        (df["start_date"] <= trip_end) &
        (df["end_date"] >= trip_start)
    ]

    # Sort for deterministic output
    df = df.sort_values(
        by=["city", "start_date", "start_time"],
        na_position="last"
    ).reset_index(drop=True)

    return df

# -------------------------------------------------
# CLI ENTRY POINT (FOR STREAMLIT)
# -------------------------------------------------

if __name__ == "__main__":

    parser = argparse.ArgumentParser(
        description="Filter events by city and trip dates"
    )

    parser.add_argument(
        "--cities",
        required=True,
        help="Comma-separated list of cities (e.g. Delhi,Agra,Goa)"
    )

    parser.add_argument(
        "--start",
        required=True,
        help="Trip start date (YYYY-MM-DD)"
    )

    parser.add_argument(
        "--end",
        required=True,
        help="Trip end date (YYYY-MM-DD)"
    )

    args = parser.parse_args()

    cities = [c.strip() for c in args.cities.split(",")]
    trip_start_date = args.start
    trip_end_date = args.end

    filtered_df = filter_events_by_city_and_date(
        cities=cities,
        trip_start_date=trip_start_date,
        trip_end_date=trip_end_date
    )

    filtered_df.to_csv(OUTPUT_CSV, index=False)

    print(f"Filtered events saved to {OUTPUT_CSV}")
    print(f"Total events found: {len(filtered_df)}")
