# visualize.py

import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
import matplotlib.dates as mdates
import random


from constants.service import (
    CSV_STREAM_DAY_PATH,
    CSV_TRACK_PATH,
    CSV_ARTIST_PATH,
    CSV_RELEASE_PATH,
    ORDER_TYPE,
)

# We load a font in order to be able to display Japanese characters
jp_prop = fm.FontProperties(fname="./data/font/NotoSansJP-Regular.ttf")
fm.fontManager.addfont("./data/font/NotoSansJP-Regular.ttf")
plt.rcParams["font.family"] = "Noto Sans JP"


# ----------------------------------------------- Track Stats -----------------------------------------------


# Return top n tracks sorted by minutes streamed or by stream count
def top_tracks(
    n: int, order_type: ORDER_TYPE, csv_tracks_path: str = CSV_TRACK_PATH
) -> pd.DataFrame:
    t_df = pd.read_csv(csv_tracks_path)
    if order_type == ORDER_TYPE.MINUTES_STREAMED:
        sorted_t_df = t_df.sort_values("Minutes_Streamed", ascending=False)
    elif order_type == ORDER_TYPE.TRACK_DONE_COUNT:
        sorted_t_df = t_df.sort_values("Track_Done_Count", ascending=False)
    return sorted_t_df.head(n)


# Return the average duration of all tracks the user listened
def average_duration(csv_tracks_path: str = CSV_TRACK_PATH) -> int:
    t_df = pd.read_csv(csv_tracks_path)
    avg_duration = t_df["Duration_Ms"].mean()
    return avg_duration / 1000


# ----------------------------------------------- Artist Stats -----------------------------------------------


# Return top n artists sorted by minutes streamed or by stream count
def top_artists(
    n: int, order_type: ORDER_TYPE, csv_artists_path: str = CSV_ARTIST_PATH
) -> pd.DataFrame:
    a_df = pd.read_csv(csv_artists_path)
    if order_type == ORDER_TYPE.MINUTES_STREAMED:
        sorted_a_df = a_df.sort_values("Minutes_Streamed", ascending=False)
    elif order_type == ORDER_TYPE.TRACK_DONE_COUNT:
        sorted_a_df = a_df.sort_values("Track_Done_Count", ascending=False)
    return sorted_a_df.head(n)


# Return the ratio of the number of track listened and the monthly listeners number of artists
def playcount_artist_popularity_ratio(csv_artists_path: str = CSV_ARTIST_PATH):
    a_df = pd.read_csv(csv_artists_path)

    filt = (a_df["Track_Done_Count"] > 50) & (a_df["Popularity"] > 0)
    a_df = a_df.loc[filt]
    a_df["Originality_Score"] = a_df["Track_Done_Count"] / a_df["Popularity"]

    return a_df[
        ["Name", "Popularity", "Track_Done_Count", "Originality_Score"]
    ].sort_values("Originality_Score", ascending=False)


# ----------------------------------------------- Releases Stats -----------------------------------------------


# Return top n albums/eps sorted by minutes streamed or by stream count
def top_releases(
    n: int, order_type: ORDER_TYPE, csv_releases_path: str = CSV_RELEASE_PATH
) -> pd.DataFrame:
    r_df = pd.read_csv(csv_releases_path)
    if order_type == ORDER_TYPE.MINUTES_STREAMED:
        sorted_r_df = r_df.sort_values("Minutes_Streamed", ascending=False)
    elif order_type == ORDER_TYPE.TRACK_DONE_COUNT:
        sorted_r_df = r_df.sort_values("Track_Done_Count", ascending=False)
    return sorted_r_df.head(n)


def plot_bar_chart(df, title):
    colors = [
        "#1f77b4",
        "#ff7f0e",
        "#2ca02c",
        "#d62728",
        "#9467bd",
        "#8c564b",
        "#e377c2",
        "#7f7f7f",
        "#bcbd22",
        "#17becf",
    ]
    rdm_colors = random.sample(colors, k=len(df))

    fig, ax = plt.subplots(figsize=(10, 6))
    ax.bar(df["Name"], df["Minutes_Streamed"], color=rdm_colors)
    ax.set_title(title, fontproperties=jp_prop)
    ax.set_xlabel("Name", fontproperties=jp_prop)
    ax.set_ylabel("Minutes Streamed", fontproperties=jp_prop)
    ax.tick_params(axis="x", rotation=90)
    return fig


def scatter_calculate_scores(artists_csv_path: str = CSV_ARTIST_PATH):
    w_click = 1.0
    w_done = 0.5
    w_skip = 0.2

    a_df = pd.read_csv(artists_csv_path)
    filt = (a_df["Track_Done_Count"] > 50) & (a_df["Click_Row_Count"] > 0)
    df = a_df.loc[filt].copy()

    df["Interest_Score"] = (
        w_done * df["Track_Done_Count"]
        + w_click * df["Click_Row_Count"]
        - w_skip * df["Skipped_Count"]
    )

    df["Commitment_Ratio"] = (df["Track_Done_Count"] + df["Click_Row_Count"]) / (
        df["Track_Done_Count"] + df["Click_Row_Count"] + df["Skipped_Count"]
    )

    fig, ax = plt.subplots(figsize=(10, 6))
    ax.scatter(df["Interest_Score"], df["Commitment_Ratio"])
    ax.set_xlabel("Interest Score")
    ax.set_ylabel("Commitment Ratio")
    ax.set_title("Interest Score vs Commitment Ratio")
    ax.plot(
        [df["Interest_Score"].min(), df["Interest_Score"].max()],
        [df["Commitment_Ratio"].min(), df["Commitment_Ratio"].max()],
        color="red",
    )

    df_selected = df[["Name", "Interest_Score", "Commitment_Ratio"]]

    plt.show()

    # return (
    #     fig,
    #     df_selected.sort_values("Interest_Score", ascending=False).head(50),
    #     df_selected.sort_values("Commitment_Ratio", ascending=False).head(50),
    # )


def scatter_playcount_duration(tracks_csv_path: str = CSV_TRACK_PATH):
    t_df = pd.read_csv(tracks_csv_path)

    fig, ax = plt.subplots(figsize=(10, 6))
    ax.scatter(t_df["Track_Done_Count"], t_df["Duration_Ms"])
    ax.set_xlabel("Tracks Playcount")
    ax.set_ylabel("Tracks Duration in Ms")
    ax.set_title("Playcount vs Duration")
    ax.plot(
        [t_df["Track_Done_Count"].min(), t_df["Track_Done_Count"].max()],
        [t_df["Duration_Ms"].min(), t_df["Duration_Ms"].max()],
        color="red",
    )
    plt.show()


def stream_day_plot_per_track_done(stream_day_csv_path: str = CSV_STREAM_DAY_PATH):
    s_d_df = pd.read_csv(stream_day_csv_path)

    # Conversion en datetime
    s_d_df["Date"] = pd.to_datetime(s_d_df["Date"])
    s_d_df.sort_values(by="Date", inplace=True)

    fig, ax = plt.subplots(figsize=(12, 6))
    ax.plot(s_d_df["Date"], s_d_df["Track_Done_Count"])

    # Titres et labels
    ax.set_title("Track done per day", fontproperties=jp_prop)
    ax.set_xlabel("Date", fontproperties=jp_prop)
    ax.set_ylabel("Number of track done", fontproperties=jp_prop)

    # Format des dates en abscisse
    ax.xaxis.set_major_locator(mdates.MonthLocator())  # une graduation par mois
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y-%m"))  # affichage AAAA-MM

    fig.autofmt_xdate()  # rotation automatique pour lisibilité

    plt.show()


def stream_day_plot_per_minutes_streamed(
    stream_day_csv_path: str = CSV_STREAM_DAY_PATH,
):
    s_d_df = pd.read_csv(stream_day_csv_path)

    # Conversion en datetime
    s_d_df["Date"] = pd.to_datetime(s_d_df["Date"])
    s_d_df.sort_values(by="Date", inplace=True)

    fig, ax = plt.subplots(figsize=(12, 6))
    ax.plot(s_d_df["Date"], s_d_df["Total_Duration_Play_m"])

    # Titres et labels
    ax.set_title("Minutes streamed per day", fontproperties=jp_prop)
    ax.set_xlabel("Date", fontproperties=jp_prop)
    ax.set_ylabel("Number of minutes streamed", fontproperties=jp_prop)

    # Format des dates en abscisse
    ax.xaxis.set_major_locator(mdates.MonthLocator())  # une graduation par mois
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y-%m"))  # affichage AAAA-MM

    fig.autofmt_xdate()  # rotation automatique pour lisibilité

    plt.show()
