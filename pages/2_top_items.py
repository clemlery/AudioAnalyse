import streamlit as st
import pandas as pd

from config import session as db_session
from streaming_history_analyser.reporting import (
    get_artists_data,
    get_releases_data,
    get_tracks_data,
)
from streaming_history_analyser.visualize import top_artists, top_releases, top_tracks
from constants.service import ORDER_TYPE

st.set_page_config(page_title="Top Items", page_icon="🏆", layout="wide")
st.title("🏆 Top Items")

user_id: str | None = st.session_state.get("user_id")
if not user_id:
    st.warning("You are not connected. Please authenticate on the Import page first.")
    st.page_link("pages/4_import_data.py", label="Go to Import", icon="🗂️")
    st.stop()


@st.cache_data(show_spinner="Loading data…", ttl=300)
def _load_tracks(uid: str) -> pd.DataFrame:
    return get_tracks_data(db_session, uid)


@st.cache_data(show_spinner="Loading data…", ttl=300)
def _load_artists(uid: str) -> pd.DataFrame:
    return get_artists_data(db_session, uid)


@st.cache_data(show_spinner="Loading data…", ttl=300)
def _load_releases(uid: str) -> pd.DataFrame:
    return get_releases_data(db_session, uid)


with st.sidebar:
    st.header("Controls")
    sort_label = st.radio(
        "Sort by",
        ["Minutes streamed", "Play count"],
        index=0,
        help="Choose how to rank items.",
    )
    n = st.slider(
        "Number of rows (n)",
        min_value=5,
        max_value=50,
        value=10,
        step=5,
        help="How many results to display on each tab.",
    )

if sort_label == "Minutes streamed":
    order = ORDER_TYPE.MINUTES_STREAMED
    metric_col = "Minutes_Streamed"
else:
    order = ORDER_TYPE.TRACK_DONE_COUNT
    metric_col = "Track_Done_Count"

tabs = st.tabs(["🎵 Tracks", "👤 Artists", "💿 Releases"])


def _guess_name_col(df: pd.DataFrame, candidates: list[str]) -> str | None:
    for c in candidates:
        if c in df.columns:
            return c
    return None


def _bar_and_table(section: str, df: pd.DataFrame, name_candidates: list[str]):
    if df.empty:
        st.info(f"No data available for **{section}**.")
        return

    name_col = _guess_name_col(df, name_candidates)
    if name_col is None:
        df = df.reset_index(drop=True)
        name_col = df.columns[0]
    try:
        chart_df = df.set_index(name_col)[[metric_col]]
    except Exception:
        st.warning("Expected columns not found; showing raw table.")
        st.dataframe(df, use_container_width=True)
    else:
        st.bar_chart(chart_df, use_container_width=True)
        st.dataframe(df, use_container_width=True)

    st.download_button(
        label=f"Download {section} (CSV)",
        data=df.to_csv(index=False).encode("utf-8"),
        file_name=f"top_{section.lower().replace(' ', '_')}.csv",
        mime="text/csv",
        use_container_width=True,
    )


with tabs[0]:
    st.subheader(f"Top Tracks — sorted by **{sort_label}** — showing {n}")
    try:
        df_tracks = top_tracks(n, order, _load_tracks(user_id))
        _bar_and_table("Tracks", df_tracks, name_candidates=["Track_Name", "Track", "Title", "Name"])
    except Exception as e:
        st.exception(e)

with tabs[1]:
    st.subheader(f"Top Artists — sorted by **{sort_label}** — showing {n}")
    try:
        df_artists = top_artists(n, order, _load_artists(user_id))
        _bar_and_table("Artists", df_artists, name_candidates=["Artist_Name", "Artist", "Name"])
    except Exception as e:
        st.exception(e)

with tabs[2]:
    st.subheader(f"Top Releases — sorted by **{sort_label}** — showing {n}")
    try:
        df_releases = top_releases(n, order, _load_releases(user_id))
        _bar_and_table(
            "Releases",
            df_releases,
            name_candidates=["Release_Name", "Album", "Album_Name", "Release", "Name"],
        )
    except Exception as e:
        st.exception(e)
