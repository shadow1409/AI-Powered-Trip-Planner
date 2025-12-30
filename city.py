# city.py
# -------------------------------------------------
# Purpose:
# Filter events by selected cities and trip duration
# Designed to be IMPORTED by Streamlit
# CLI kept only for local debugging
# -------------------------------------------------

import pandas as pd
import argparse
from typing import List

# -------------------------------------------------
# CONFIG
# -------------------------------------------------

CSV_FILE = "india_events_2000_tourism_2026_latlon.csv"
OUTPUT_CSV = "filtered.csv"
DATE_FMT = "%Y-%m-%d"

# -------------------------------------------------
# CORE FUNCTION (STREAMLIT WILL USE THIS)
# -------------------------------------------------

def filter_events_by_city_and_date(
    cities: List[str],
    trip_start_date: str,
    trip_end_date: str
) -> pd.DataFrame:
    """
    Filters events by:
    1. Selected cities
    2. Trip date overlap
    """

    # Load dataset
    df = pd.read_csv(CSV_FILE)

    # -------------------------------
    # Normalize city values (CRITICAL)
    # -------------------------------
    df["city"] = df["city"].astype(str).str.strip()
    df["city_norm"] = df["city"].str.lower()

    cities_norm = [
        c.strip().lower()
        for c in cities
        if c and c.strip()
    ]

    if not cities_norm:
        # No cities selected → return empty DF safely
        return df.iloc[0:0]

    # -------------------------------
    # Date parsing (STRICT ISO)
    # -------------------------------
    df["start_date"] = pd.to_datetime(
        df["start_date"],
        format=DATE_FMT,
        errors="coerce"
    )
    df["end_date"] = pd.to_datetime(
        df["end_date"],
        format=DATE_FMT,
        errors="coerce"
    )

    df = df.dropna(subset=["start_date", "end_date"])

    trip_start = pd.to_datetime(trip_start_date, format=DATE_FMT)
    trip_end = pd.to_datetime(trip_end_date, format=DATE_FMT)

    # -------------------------------
    # FILTERS (THIS FIXES YOUR BUG)
    # -------------------------------
    df = df[df["city_norm"].isin(cities_norm)]

    df = df[
        (df["start_date"] <= trip_end) &
        (df["end_date"] >= trip_start)
    ]

    # Cleanup
    df = df.drop(columns=["city_norm"])

    # Stable ordering
    df = df.sort_values(
        by=["city", "start_date", "start_time"],
        na_position="last"
    ).reset_index(drop=True)

    return df


# -------------------------------------------------
# HELPER FUNCTION (USED BY app.py)
# -------------------------------------------------

def run_city_filter(
    cities: List[str],
    trip_start_date: str,
    trip_end_date: str,
    output_csv: str = OUTPUT_CSV
) -> None:
    """
    Wrapper used by Streamlit app.
    Writes filtered.csv as side-effect.
    """

    df = filter_events_by_city_and_date(
        cities=cities,
        trip_start_date=trip_start_date,
        trip_end_date=trip_end_date
    )

    df.to_csv(output_csv, index=False)


# -------------------------------------------------
# CLI ENTRY POINT (OPTIONAL, LOCAL TESTING ONLY)
# -------------------------------------------------

if __name__ == "__main__":

    parser = argparse.ArgumentParser(
        description="Filter events by city and trip dates"
    )
    parser.add_argument("--cities", required=True)
    parser.add_argument("--start", required=True)
    parser.add_argument("--end", required=True)

    args = parser.parse_args()

    city_list = [
        c.strip()
        for c in args.cities.split(",")
        if c.strip()
    ]

    df = filter_events_by_city_and_date(
        cities=city_list,
        trip_start_date=args.start,
        trip_end_date=args.end
    )

    df.to_csv(OUTPUT_CSV, index=False)

    print(f"Filtered events saved to {OUTPUT_CSV}")
    print(f"Total events found: {len(df)}")
    print(f"Cities found: {sorted(df['city'].unique().tolist())}")
