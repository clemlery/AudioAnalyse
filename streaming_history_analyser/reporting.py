# reporting.py

import csv
import os
from collections import defaultdict
from sqlalchemy import func, or_

from config import session
from constants.service import RELEASE_TYPE, CSV_BASE_DIR
from models.sql_alchemy_models.artist_sql_model import Artist
from models.sql_alchemy_models.metrics import ArtistMetricsSnapshot, TrackMetricsSnapshot
from models.sql_alchemy_models.release_sql_model import Release
from models.sql_alchemy_models.spotify_track_sql_model import SpotifyTrack
from models.sql_alchemy_models.track_sql_model import Track
from models.sql_alchemy_models.track_stream_day_sql_model import TrackStreamDay
from models.sql_alchemy_models.track_stream_sql_model import TrackStream


def artists_data_to_csv(session, user_id: str, output_file: str | None = None):
    """
    Export aggregated stream and release statistics for a given user to a CSV file.

    Args:
        session: SQLAlchemy session object
        user_id: Spotify user ID to filter stream data
        output_file: Path to the output CSV file (defaults to data/csv/{user_id}/artists_data.csv)
    """
    if output_file is None:
        output_file = f"{CSV_BASE_DIR}/{user_id}/artists_data.csv"
    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    # Define the output columns
    fieldnames = [
        "Artist_Id",
        "Name",
        "Genres",
        "Popularity",
        "Followers",
        "Minutes_Streamed",
        "Click_Row_Count",
        "Skipped_Count",
        "Track_Done_Count",
        "Track_Count",
        "Single_Number",
        "Album_Number",
        "EP_Number",
        "Monthly_Listeners",
    ]

    # Initialize stats with defaults for each artist
    stats = defaultdict(
        lambda: {
            "Artist_Id": 0,
            "Name": None,
            "Genres": None,
            "Popularity": None,
            "Followers": None,
            "Minutes_Streamed": 0,
            "Click_Row_Count": 0,
            "Skipped_Count": 0,
            "Track_Done_Count": 0,
            "Track_Count": 0,
            "Single_Number": 0,
            "Album_Number": 0,
            "EP_Number": 0,
            "Monthly_Listeners": 0,
        }
    )

    # Aggregate stream data per artist, filtered to this user
    stream_q = (
        session.query(
            Artist.id.label("artist_id"),
            Artist.name,
            Artist.genres,
            Artist.popularity,
            Artist.followers,
            func.sum(TrackStream.total_duration_play_s).label("minutes_streamed"),
            func.sum(TrackStream.click_row_count).label("click_count"),
            func.sum(TrackStream.skipped_count).label("skipped_count"),
            func.sum(TrackStream.track_done_count).label("track_done_count"),
            func.count(TrackStream.track_id).label("track_count"),
            ArtistMetricsSnapshot.monthly_listeners.label("monthly_listeners"),
        )
        .join(Artist.tracks)
        .join(Track.streams)
        .join(Artist.artist_metrics)
        .filter(TrackStream.user_id == user_id)
        .group_by(Artist.id, ArtistMetricsSnapshot.monthly_listeners)
    )

    for row in stream_q:
        stats[row.artist_id].update(
            {
                "Artist_Id": row.artist_id,
                "Name": row.name,
                "Genres": ",".join(row.genres)
                if isinstance(row.genres, (list, tuple))
                else row.genres,
                "Popularity": row.popularity,
                "Followers": row.followers,
                "Minutes_Streamed": row.minutes_streamed // 60 or 0,
                "Click_Row_Count": row.click_count or 0,
                "Skipped_Count": row.skipped_count or 0,
                "Track_Done_Count": row.track_done_count or 0,
                "Track_Count": row.track_count or 0,
                "Monthly_Listeners": row.monthly_listeners,
            }
        )

    # Aggregate release counts — scoped to artists this user has actually streamed
    streamed_artist_ids = set(stats.keys())
    release_q = (
        session.query(
            Artist.id.label("artist_id"),
            Release.release_type.label("release_type"),
            func.count(Release.id).label("count"),
        )
        .join(Release.artists)
        .filter(Artist.id.in_(streamed_artist_ids))
        .group_by(Artist.id, Release.release_type)
    )

    for artist_id_, rtype, count in release_q:
        entry = stats[artist_id_]
        if rtype == RELEASE_TYPE.SINGLE.value:
            entry["Single_Number"] = count
        elif rtype == RELEASE_TYPE.ALBUM.value:
            entry["Album_Number"] = count
        elif rtype == RELEASE_TYPE.EP.value:
            entry["EP_Number"] = count

    # Write out to CSV
    with open(output_file, "w", newline="", encoding="utf-8") as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        for data in stats.values():
            writer.writerow(data)

    print(f"Exported data for {len(stats)} artists to {output_file}")


def tracks_data_to_csv(session, user_id: str, output_file: str | None = None):
    """
    Export aggregated stream statistics for a given user to a CSV file.

    Args:
        session: SQLAlchemy session object
        user_id: Spotify user ID to filter stream data
        output_file: Path to the output CSV file (defaults to data/csv/{user_id}/tracks_data.csv)
    """
    if output_file is None:
        output_file = f"{CSV_BASE_DIR}/{user_id}/tracks_data.csv"
    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    # Define the output columns
    fieldnames = [
        "Track_Id",
        "Name",
        "Duration_Ms",
        "First_Played_At",
        "Last_Played_At",
        "Track_Done_Count",
        "Skipped_Count",
        "Click_Row_Count",
        "Minutes_Streamed",
        "Global_Playcount",
        "Artist_Id",
    ]

    # Initialize stats with defaults for each track
    stats = defaultdict(
        lambda: {
            "Track_Id": 0,
            "Name": None,
            "Duration_Ms": 0,
            "First_Played_At": "",
            "Last_Played_At": "",
            "Minutes_Streamed": 0,
            "Click_Row_Count": 0,
            "Skipped_Count": 0,
            "Track_Done_Count": 0,
            "Global_Playcount": 0,
            "Artist_Id": 0,
        }
    )

    # Aggregate stream data per track, filtered to this user
    stream_q = (
        session.query(
            Track.id.label("track_id"),
            Track.name,
            Track.duration_ms,
            TrackStream.first_played_at.label("last_play"),
            TrackStream.last_played_at.label("first_play"),
            func.sum(TrackStream.total_duration_play_s).label("minutes_streamed"),
            func.sum(TrackStream.click_row_count).label("click_count"),
            func.sum(TrackStream.skipped_count).label("skipped_count"),
            func.sum(TrackStream.track_done_count).label("track_done_count"),
            TrackMetricsSnapshot.playcount.label("track_global_playcount"),
            Artist.id.label("artist_id"),
        )
        .join(Track.streams)
        .join(Track.track_metrics)
        .join(Track.artists)
        .filter(TrackStream.user_id == user_id)
        .group_by(
            Track.id,
            TrackMetricsSnapshot.playcount,
            TrackStream.first_played_at,
            TrackStream.last_played_at,
            Artist.id,
        )
    )

    for row in stream_q:
        stats[row.track_id].update(
            {
                "Track_Id": row.track_id,
                "Name": row.name,
                "Duration_Ms": row.duration_ms,
                "First_Played_At": row.first_play,
                "Last_Played_At": row.last_play,
                "Minutes_Streamed": row.minutes_streamed // 60 or 0,
                "Click_Row_Count": row.click_count or 0,
                "Skipped_Count": row.skipped_count or 0,
                "Track_Done_Count": row.track_done_count or 0,
                "Global_Playcount": row.track_global_playcount or 0,
                "Artist_Id": row.artist_id,
            }
        )

    # Write out to CSV
    with open(output_file, "w", newline="", encoding="utf-8") as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        for data in stats.values():
            writer.writerow(data)

    print(f"Exported data for {len(stats)} track to {output_file}")


def releases_data_to_csv(session, user_id: str, output_file: str | None = None):
    if output_file is None:
        output_file = f"{CSV_BASE_DIR}/{user_id}/releases_data.csv"
    os.makedirs(os.path.dirname(output_file), exist_ok=True)

    # Define the output columns
    fieldnames = [
        "Name",
        "Release_Type",
        "Popularity",
        "Total_Duration_m",
        "Release_Date",
        "Total_Tracks",
        "Track_Done_Count",
        "Skipped_Count",
        "Click_Row_Count",
        "Minutes_Streamed",
    ]

    # Initialize stats with defaults for each track
    stats = defaultdict(
        lambda: {
            "Name": None,
            "Release_Type": None,
            "Popularity": 0,
            "Total_Duration_m": 0,
            "Minutes_Streamed": 0,
            "Click_Row_Count": 0,
            "Skipped_Count": 0,
            "Track_Done_Count": 0,
            "Total_Tracks": 0,
            "Release_Date": None,
        }
    )

    # Aggregate stream data per release (all release)
    stream_q = (
        session.query(
            Release.id.label("release_id"),
            Release.name,
            Release.popularity,
            Release.release_date,
            Release.total_tracks,
            Release.release_type,
            func.sum(Track.duration_ms).label("total_duration_ms"),
            func.sum(TrackStream.total_duration_play_s).label("secondes_streamed"),
            func.sum(TrackStream.click_row_count).label("click_count"),
            func.sum(TrackStream.skipped_count).label("skipped_count"),
            func.sum(TrackStream.track_done_count).label("track_done_count"),
        )
        .join(Release.spotify_tracks)
        .join(SpotifyTrack.canonical)
        .join(Track.streams)
        .filter(or_(Release.release_type == "album", Release.release_type == "ep"))
        .filter(TrackStream.user_id == user_id)
        .group_by(Release.id)
    )

    for row in stream_q:
        stats[row.release_id].update(
            {
                "Name": row.name or None,
                "Release_Type": row.release_type or None,
                "Popularity": row.popularity or 0,
                "Total_Duration_m": row.total_duration_ms // 60000 or 0,
                "Minutes_Streamed": row.secondes_streamed // 60 or 0,
                "Click_Row_Count": row.click_count or 0,
                "Skipped_Count": row.skipped_count or 0,
                "Track_Done_Count": row.track_done_count or 0,
                "Total_Tracks": row.total_tracks or 0,
                "Release_Date": row.release_date or None,
            }
        )

    # Write out to CSV
    with open(output_file, "w", newline="", encoding="utf-8") as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        for data in stats.values():
            writer.writerow(data)

    print(f"Exported data for {len(stats)} release to {output_file}")


def track_stream_day_to_csv(session, user_id: str, output_file: str | None = None):
    if output_file is None:
        output_file = f"{CSV_BASE_DIR}/{user_id}/stream_day_data.csv"
    os.makedirs(os.path.dirname(output_file), exist_ok=True)

    fieldnames = [
        "Date",
        "Track_Done_Count",
        "Skipped_Count",
        "Click_Row_Count",
        "Total_Duration_Play_m",
    ]

    stats = defaultdict(
        lambda: {
            "Date": "",
            "Track_Done_Count": 0,
            "Skipped_Count": 0,
            "Click_Row_Count": 0,
            "Total_Duration_Play_m": 0,
        }
    )

    stream_q = (
        session.query(
            TrackStreamDay.date,
            func.sum(TrackStreamDay.track_done_count).label("track_done_count"),
            func.sum(TrackStreamDay.skipped_count).label("skipped_count"),
            func.sum(TrackStreamDay.click_row_count).label("click_count"),
            func.sum(TrackStreamDay.total_duration_play_s).label("secondes_streamed"),
        )
        .filter(TrackStreamDay.user_id == user_id)
        .group_by(TrackStreamDay.date)
    )

    for row in stream_q:
        stats[row.date].update(
            {
                "Date": row.date or "",
                "Track_Done_Count": row.track_done_count or 0,
                "Skipped_Count": row.skipped_count or 0,
                "Click_Row_Count": row.click_count or 0,
                "Total_Duration_Play_m": row.secondes_streamed // 60 or 0,
            }
        )

    with open(output_file, "w", newline="", encoding="utf-8") as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        for data in stats.values():
            writer.writerow(data)
