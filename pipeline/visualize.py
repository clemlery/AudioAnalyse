# visualize.py

import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
import matplotlib.dates as mdates
import random

from constants.service import ORDER_TYPE

# We load a font in order to be able to display Japanese characters
jp_prop = fm.FontProperties(fname="./data/font/NotoSansJP-Regular.ttf")
fm.fontManager.addfont("./data/font/NotoSansJP-Regular.ttf")
plt.rcParams["font.family"] = "Noto Sans JP"


# ----------------------------------------------- Track Stats -----------------------------------------------


def top_tracks(n: int, order_type: ORDER_TYPE, df: pd.DataFrame) -> pd.DataFrame:
    if order_type == ORDER_TYPE.MINUTES_STREAMED:
        return df.sort_values("Minutes_Streamed", ascending=False).head(n)
    return df.sort_values("Track_Done_Count", ascending=False).head(n)


def average_duration(df: pd.DataFrame) -> float:
    return df["Duration_Ms"].mean() / 1000


# ----------------------------------------------- Artist Stats -----------------------------------------------


def top_artists(n: int, order_type: ORDER_TYPE, df: pd.DataFrame) -> pd.DataFrame:
    if order_type == ORDER_TYPE.MINUTES_STREAMED:
        return df.sort_values("Minutes_Streamed", ascending=False).head(n)
    return df.sort_values("Track_Done_Count", ascending=False).head(n)


def playcount_artist_popularity_ratio(df: pd.DataFrame) -> pd.DataFrame:
    filt = (df["Track_Done_Count"] > 50) & (df["Popularity"] > 0)
    df = df.loc[filt].copy()
    df["Originality_Score"] = df["Track_Done_Count"] / df["Popularity"]
    return df[["Name", "Popularity", "Track_Done_Count", "Originality_Score"]].sort_values(
        "Originality_Score", ascending=False
    )


# ----------------------------------------------- Releases Stats -----------------------------------------------


def top_releases(n: int, order_type: ORDER_TYPE, df: pd.DataFrame) -> pd.DataFrame:
    if order_type == ORDER_TYPE.MINUTES_STREAMED:
        return df.sort_values("Minutes_Streamed", ascending=False).head(n)
    return df.sort_values("Track_Done_Count", ascending=False).head(n)


def plot_bar_chart(df: pd.DataFrame, title: str):
    colors = [
        "#1f77b4", "#ff7f0e", "#2ca02c", "#d62728", "#9467bd",
        "#8c564b", "#e377c2", "#7f7f7f", "#bcbd22", "#17becf",
    ]
    rdm_colors = random.sample(colors, k=len(df))

    fig, ax = plt.subplots(figsize=(10, 6))
    ax.bar(df["Name"], df["Minutes_Streamed"], color=rdm_colors)
    ax.set_title(title, fontproperties=jp_prop)
    ax.set_xlabel("Name", fontproperties=jp_prop)
    ax.set_ylabel("Minutes Streamed", fontproperties=jp_prop)
    ax.tick_params(axis="x", rotation=90)
    return fig


# ----------------------------------------------- Stream Day Stats -----------------------------------------------


def stream_day_plot_per_track_done(df: pd.DataFrame):
    df = df.copy()
    df["Date"] = pd.to_datetime(df["Date"])
    df.sort_values(by="Date", inplace=True)

    fig, ax = plt.subplots(figsize=(12, 6))
    ax.plot(df["Date"], df["Track_Done_Count"])
    ax.set_title("Track done per day", fontproperties=jp_prop)
    ax.set_xlabel("Date", fontproperties=jp_prop)
    ax.set_ylabel("Number of track done", fontproperties=jp_prop)
    ax.xaxis.set_major_locator(mdates.MonthLocator())
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y-%m"))
    fig.autofmt_xdate()
    return fig


def stream_day_plot_per_minutes_streamed(df: pd.DataFrame):
    df = df.copy()
    df["Date"] = pd.to_datetime(df["Date"])
    df.sort_values(by="Date", inplace=True)

    fig, ax = plt.subplots(figsize=(12, 6))
    ax.plot(df["Date"], df["Total_Duration_Play_m"])
    ax.set_title("Minutes streamed per day", fontproperties=jp_prop)
    ax.set_xlabel("Date", fontproperties=jp_prop)
    ax.set_ylabel("Number of minutes streamed", fontproperties=jp_prop)
    ax.xaxis.set_major_locator(mdates.MonthLocator())
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y-%m"))
    fig.autofmt_xdate()
    return fig
