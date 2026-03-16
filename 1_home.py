# 1_Home.py
import streamlit as st

# We import other pages
from pages import *

st.set_page_config(
    page_title="Lyra — Spotify Analytics",
    page_icon="🎧",
    layout="wide",
)

st.title("🎧 Lyra — Spotify Listening Analytics")

# Session indicator
user_id = st.session_state.get("user_id")
if user_id:
    display_name = st.session_state.get("display_name", user_id)
    st.caption(f"Connected as **{display_name}**")
else:
    st.warning(
        "You are not connected. Go to **Import Data** to authenticate with Spotify.",
        icon="🔒",
    )

st.markdown(
    """
Welcome! Follow the steps below to import your data and explore your Spotify statistics.

**Recommended workflow:**
1. **Import / connect** your Spotify account and upload your extended streaming history.
2. **Explore the top charts** (artists, tracks, releases).
3. **Analyze custom scores** (Interest Score & Commitment Ratio).
"""
)

with st.container():
    c1, c2, c3 = st.columns(3)

    with c1:
        st.subheader("1) Import Data")
        st.write(
            "Connect your Spotify account and upload the extended history files "
            "provided by Spotify."
        )
        st.page_link(
            "./pages/4_import_data.py",  # opens the import page
            label="Go to Import",
            icon="🗂️",
            use_container_width=True,
        )
        st.caption("This page checks file naming and saves them on the server.")

    with c2:
        st.subheader("2) Top Artists / Tracks / Releases")
        st.write(
            "View your **Top 10** by listening time (artists, tracks, releases) "
            "with bar charts."
        )
        st.page_link(
            "./pages/2_top_items.py",
            label="View Top Charts",
            icon="🏆",
            use_container_width=True,
        )
        st.caption("Bar charts generated with built-in visualization functions.")

    with c3:
        st.subheader("3) Custom Scores")
        st.write(
            "Compare **Interest Score** and **Commitment Ratio** for artists, tracks, "
            "and releases, with scatter plots and sorted tables."
        )
        st.page_link(
            "./pages/3_custom_values.py",
            label="Analyze Scores",
            icon="📈",
            use_container_width=True,
        )
        st.caption(
            "Based on CSV files: `artists_data.csv`, `tracks_data.csv`, `releases_data.csv`."
        )

st.divider()
st.markdown(
    """
### Usage Tips
- Start with **Import Data** if this is your first time.
- Make sure your environment variables (CLIENT_ID, REDIRECT_URI, etc.) are correctly set for Spotify authentication.
- You can always come back to this page to navigate between sections.
"""
)

st.markdown("> Happy analyzing! 🎶")
