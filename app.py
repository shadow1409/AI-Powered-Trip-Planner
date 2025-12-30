import streamlit as st
import subprocess
import json
import pandas as pd
from datetime import date

# --------------------------------------------
# CONFIG
# --------------------------------------------

EVENTS_CSV = "india_events_2000_tourism_2026_latlon.csv"
YEAR_START = date(2026, 1, 1)
YEAR_END = date(2026, 12, 31)

# --------------------------------------------
# LOAD CITY LIST
# --------------------------------------------

df_events = pd.read_csv(EVENTS_CSV)
REAL_CITIES = sorted(df_events["city"].unique())

# --------------------------------------------
# STREAMLIT UI
# --------------------------------------------

st.set_page_config(page_title="AI Trip Planner", layout="wide")

st.markdown(
    "<h1 style='text-align:center;'>🧠 AI-Powered Trip Planner</h1>",
    unsafe_allow_html=True
)

# -------- Trip Dates --------
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

# -------- Cities (MULTISELECT – STABLE) --------
st.subheader("📍 Select Cities")

selected_cities = st.multiselect(
    "Choose cities to visit",
    REAL_CITIES,
    default=[]
)

# -------- Interests --------
st.subheader("✨ Your Interests")

interest_text = st.text_area(
    "Describe what you enjoy",
    height=120,
    placeholder="I love beaches, cultural places, peaceful environments..."
)

# --------------------------------------------
# RUN PIPELINE
# --------------------------------------------

if st.button("🚀 Generate Trip Plan"):

    if not interest_text.strip():
        st.error("Please describe your interests.")
        st.stop()

    if not selected_cities:
        st.error("Please select at least one city.")
        st.stop()

    with st.status("Running planning pipeline...", expanded=True) as status:

        status.write("🔹 Understanding your interests...")
        subprocess.run(
            ["python", "gemini.py", "--interest", interest_text],
            check=True
        )

        status.write("🔹 Filtering events by city and date...")
        subprocess.run(
            [
                "python", "city.py",
                "--cities", ",".join(selected_cities),
                "--start", str(trip_start),
                "--end", str(trip_end)
            ],
            check=True
        )

        status.write("🔹 Computing relevance scores...")
        subprocess.run(["python", "relevance.py"], check=True)

        status.write("🔹 Building trip plan...")
        subprocess.run(
            [
                "python", "planner.py",
                "--start", str(trip_start),
                "--end", str(trip_end)
            ],
            check=True
        )

        status.write("🔹 Creating final itinerary...")
        subprocess.run(["python", "gemini_itinerary.py"], check=True)

        status.update(label="✅ Trip plan ready!", state="complete")

    # --------------------------------------------
    # DISPLAY RESULT
    # --------------------------------------------

    st.divider()
    st.header("🗺️ Your Trip Itinerary")

    with open("itinerary.json", "r", encoding="utf-8") as f:
        itinerary = json.load(f)

    st.markdown(
        f"**Trip Dates:** {itinerary['trip_summary']['start_date']} → "
        f"{itinerary['trip_summary']['end_date']}"
    )

    for city_block in itinerary["itinerary"]:
        with st.expander(f"📍 {city_block['city']}"):
            st.write(city_block["city_overview"])
            for act in city_block["activities"]:
                st.markdown(
                    f"""
                    **• {act['title']}**  
                    _{act['date_info']}_  
                    {act['description']}
                    """
                )
