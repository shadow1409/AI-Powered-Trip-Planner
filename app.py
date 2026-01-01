import streamlit as st
import subprocess
import json
import pandas as pd
from datetime import date
import sys

# --------------------------------------------
# CONFIG
# --------------------------------------------

EVENTS_CSV = "india_events_2000_tourism_2026_latlon.csv"
YEAR_START = date(2026, 1, 1)
YEAR_END = date(2026, 12, 31)
PYTHON_BIN = sys.executable  # cloud-safe

# --------------------------------------------
# PAGE SETUP (NORMAL)
# --------------------------------------------

st.set_page_config(
    page_title="AI-Powered Trip Planner",
    layout="centered"
)

# --------------------------------------------
# LOAD CITY LIST
# --------------------------------------------

df_events = pd.read_csv(EVENTS_CSV)
REAL_CITIES = sorted(df_events["city"].dropna().unique())

# --------------------------------------------
# HEADER
# --------------------------------------------

st.title("🧠 AI-Powered Trip Planner")
st.caption("Plan intelligent, interest-aware trips across Indian cities.")

st.divider()

# --------------------------------------------
# INPUTS
# --------------------------------------------

st.subheader("📅 Trip Duration")

col1, col2 = st.columns(2)
with col1:
    trip_start = st.date_input(
        "Trip Start Date",
        min_value=YEAR_START,
        max_value=YEAR_END,
        value=YEAR_START
    )

with col2:
    trip_end = st.date_input(
        "Trip End Date",
        min_value=trip_start,
        max_value=YEAR_END,
        value=trip_start
    )

st.subheader("📍 Select Cities")

selected_cities = st.multiselect(
    "Choose cities to visit",
    REAL_CITIES
)

st.subheader("✨ Your Interests")

interest_text = st.text_area(
    "Describe what you enjoy",
    height=120,
    placeholder="I love music, heritage walks, beaches, tech expos…"
)

st.divider()

# --------------------------------------------
# RUN PIPELINE
# --------------------------------------------

generate = st.button("🚀 Generate Trip Plan", use_container_width=True)

if generate:

    if not interest_text.strip():
        st.error("Please describe your interests.")
        st.stop()

    if not selected_cities:
        st.error("Please select at least one city.")
        st.stop()

    safe_interest = interest_text.replace("\n", " ").replace('"', "'").strip()

    with st.status("Planning your trip...", expanded=True) as status:

        try:
            status.write("Understanding your interests…")
            subprocess.run(
                [PYTHON_BIN, "gemini.py", "--interest", safe_interest],
                check=True
            )

            status.write("Filtering events by city and date…")
            subprocess.run(
                [
                    PYTHON_BIN, "city.py",
                    "--cities", ",".join(selected_cities),
                    "--start", str(trip_start),
                    "--end", str(trip_end)
                ],
                check=True
            )

            status.write("Computing relevance scores…")
            subprocess.run(
                [PYTHON_BIN, "relevance.py"],
                check=True
            )

            status.write("Building trip plan…")
            subprocess.run(
                [
                    PYTHON_BIN, "planner.py",
                    "--start", str(trip_start),
                    "--end", str(trip_end)
                ],
                check=True
            )

            status.write("Creating final itinerary…")
            subprocess.run(
                [PYTHON_BIN, "gemini_itinerary.py"],
                check=True
            )

            status.update(label="✅ Trip plan ready!", state="complete")

        except subprocess.CalledProcessError as e:
            st.error("Pipeline failed.")
            st.code(e.stderr or e.stdout)
            st.stop()

    # --------------------------------------------
    # DISPLAY RESULTS
    # --------------------------------------------

    with open("itinerary.json", "r", encoding="utf-8") as f:
        itinerary = json.load(f)

    st.divider()
    st.header("🗺️ Your Trip Itinerary")

    st.markdown(
        f"""
        **📅 Dates:** {itinerary['trip_summary']['start_date']} → {itinerary['trip_summary']['end_date']}  
        **📍 Cities:** {", ".join(itinerary['trip_summary']['cities_covered'])}
        """
    )

    for city in itinerary["itinerary"]:
        with st.expander(f"📍 {city['city']}"):
            st.write(city["city_overview"])
            st.write(f"**Why visit:** {city['city_reason']}")

            for act in city["activities"]:
                st.markdown(
                    f"""
                    **• {act['title']}**  
                    _{act['date_info']}_  
                    {act['description']}  
                    *{act['relevance_note']}*
                    """
                )
