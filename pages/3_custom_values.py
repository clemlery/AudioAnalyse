import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

from config import session as db_session
from streaming_history_analyser.reporting import get_artists_data, get_tracks_data

user_id: str | None = st.session_state.get("user_id")
if not user_id:
    st.warning("You are not connected. Please authenticate on the Import page first.")
    st.page_link("pages/4_import_data.py", label="Go to Import", icon="🗂️")
    st.stop()


@st.cache_data(show_spinner="Loading data…", ttl=300)
def _load_artists(uid: str) -> pd.DataFrame:
    return get_artists_data(db_session, uid)


@st.cache_data(show_spinner="Loading data…", ttl=300)
def _load_tracks(uid: str) -> pd.DataFrame:
    return get_tracks_data(db_session, uid)


# ---------------------------
# Sidebar: global controls
# ---------------------------
with st.sidebar:
    st.header("Settings")

    st.subheader("Interest Score Weights")
    w_click = st.number_input("w_click", min_value=0.0, value=1.0, step=0.1)
    w_done = st.number_input("w_done", min_value=0.0, value=0.5, step=0.1)
    w_skip = st.number_input("w_skip", min_value=0.0, value=0.2, step=0.1)

    st.subheader("Filters")
    min_done = st.number_input(
        "Minimum Track_Done_Count", min_value=0, value=50, step=5
    )
    require_clicks = st.checkbox("Require Click_Row_Count > 0", value=True)

    st.subheader("Top tables")
    top_n = st.slider("Top N rows", min_value=5, max_value=100, value=50, step=5)


def diag_minmax(ax, x, y):
    try:
        ax.plot([x.min(), x.max()], [y.min(), y.max()])
    except Exception:
        pass


def df_download_button(df: pd.DataFrame, label: str, filename: str):
    st.download_button(
        label=label,
        data=df.to_csv(index=False).encode("utf-8"),
        file_name=filename,
        mime="text/csv",
        use_container_width=True,
    )


# ---------------------------
# Tabs
# ---------------------------
t1, t2 = st.tabs(
    ["🎯 Interest vs Commitment (Artists)", "⏱️ Playcount vs Duration (Tracks)"]
)

# ===========================================================
# TAB 1 — Interest Score vs Commitment Ratio (Artists)
# ===========================================================
with t1:
    st.subheader("Interest Score vs Commitment Ratio — Artists")

    try:
        a_df = _load_artists(user_id)
    except Exception as e:
        st.exception(e)
        st.stop()

    needed_cols = {"Name", "Track_Done_Count", "Click_Row_Count", "Skipped_Count"}
    missing = needed_cols - set(a_df.columns)
    if missing:
        st.error(f"Missing columns in artists data: {', '.join(sorted(missing))}")
        st.stop()

    filt = a_df["Track_Done_Count"] > min_done
    if require_clicks:
        filt &= a_df["Click_Row_Count"] > 0
    df = a_df.loc[filt].copy()

    df["Interest_Score"] = (
        w_done * df["Track_Done_Count"]
        + w_click * df["Click_Row_Count"]
        - w_skip * df["Skipped_Count"]
    )
    denom = df["Track_Done_Count"] + df["Click_Row_Count"] + df["Skipped_Count"]
    denom = denom.replace(0, np.nan)
    df["Commitment_Ratio"] = (df["Track_Done_Count"] + df["Click_Row_Count"]) / denom
    df = df.dropna(subset=["Commitment_Ratio"])

    c1, c2 = st.columns([2, 1])

    with c1:
        st.markdown("#### Scatter plot")
        fig, ax = plt.subplots(figsize=(10, 6))
        ax.scatter(df["Interest_Score"], df["Commitment_Ratio"])
        ax.set_xlabel("Interest Score")
        ax.set_ylabel("Commitment Ratio")
        ax.set_title("Interest Score vs Commitment Ratio")
        diag_minmax(ax, df["Interest_Score"], df["Commitment_Ratio"])
        st.pyplot(fig, use_container_width=True)

    with c2:
        st.markdown("#### Options")
        annotate = st.checkbox(
            "Annotate top points",
            value=True,
            help="Show labels for highest Interest Score & Commitment Ratio.",
        )
        show_raw = st.checkbox("Show raw filtered table", value=False)

    top_interest = (
        df[["Name", "Interest_Score", "Commitment_Ratio"]]
        .sort_values("Interest_Score", ascending=False)
        .head(top_n)
    )
    top_commitment = (
        df[["Name", "Interest_Score", "Commitment_Ratio"]]
        .sort_values("Commitment_Ratio", ascending=False)
        .head(top_n)
    )

    if annotate and not df.empty:
        best_i = top_interest.iloc[0]
        best_c = top_commitment.iloc[0]
        ax.annotate(best_i["Name"], (best_i["Interest_Score"], best_i["Commitment_Ratio"]))
        ax.annotate(best_c["Name"], (best_c["Interest_Score"], best_c["Commitment_Ratio"]))
        st.pyplot(fig, use_container_width=True)

    st.markdown("#### Top tables")
    cti, ctc = st.columns(2)
    with cti:
        st.write(f"Top {len(top_interest)} by Interest Score")
        st.dataframe(top_interest, use_container_width=True)
        df_download_button(top_interest, "Download Top by Interest (CSV)", "top_interest_artists.csv")
    with ctc:
        st.write(f"Top {len(top_commitment)} by Commitment Ratio")
        st.dataframe(top_commitment, use_container_width=True)
        df_download_button(top_commitment, "Download Top by Commitment (CSV)", "top_commitment_artists.csv")

    if show_raw:
        st.markdown("#### Filtered raw data")
        st.dataframe(df.sort_values("Interest_Score", ascending=False), use_container_width=True)
        df_download_button(df, "Download Filtered (CSV)", "artists_filtered.csv")

# ===========================================================
# TAB 2 — Playcount vs Duration (Tracks)
# ===========================================================
with t2:
    st.subheader("Playcount vs Duration — Tracks")

    try:
        t_df = _load_tracks(user_id)
    except Exception as e:
        st.exception(e)
        st.stop()

    needed_cols = {"Track_Done_Count", "Duration_Ms"}
    missing = needed_cols - set(t_df.columns)
    if missing:
        st.error(f"Missing columns in tracks data: {', '.join(sorted(missing))}")
        st.stop()

    c1, c2, c3 = st.columns(3)
    with c1:
        use_log_x = st.checkbox("Log scale X (plays)", value=False)
    with c2:
        to_minutes = st.checkbox("Show duration in minutes", value=True)
    with c3:
        show_table = st.checkbox("Show table & download", value=False)

    plot_df = t_df.copy()
    if to_minutes:
        plot_df["Duration_Min"] = plot_df["Duration_Ms"] / 60000.0
        y_col = "Duration_Min"
        y_label = "Track Duration (minutes)"
    else:
        y_col = "Duration_Ms"
        y_label = "Track Duration (ms)"

    fig2, ax2 = plt.subplots(figsize=(10, 6))
    ax2.scatter(plot_df["Track_Done_Count"], plot_df[y_col])
    ax2.set_xlabel("Track Playcount")
    ax2.set_ylabel(y_label)
    ax2.set_title("Playcount vs Duration")
    diag_minmax(ax2, plot_df["Track_Done_Count"], plot_df[y_col])
    if use_log_x:
        try:
            ax2.set_xscale("log")
        except Exception:
            pass
    st.pyplot(fig2, use_container_width=True)

    if show_table:
        cols = [
            c for c in ["Name", "Artist_Name", "Track_Done_Count", y_col, "Duration_Ms"]
            if c in plot_df.columns
        ]
        st.dataframe(
            plot_df[cols].sort_values("Track_Done_Count", ascending=False),
            use_container_width=True,
        )
        df_download_button(plot_df[cols], "Download tracks view (CSV)", "tracks_playcount_duration.csv")

st.caption(
    "Notes: Interest Score = w_done*Track_Done_Count + w_click*Click_Row_Count - w_skip*Skipped_Count; "
    "Commitment Ratio = (Track_Done_Count + Click_Row_Count) / (Track_Done_Count + Click_Row_Count + Skipped_Count)."
)
