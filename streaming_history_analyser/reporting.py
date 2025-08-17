# graph.py

# We import the DAOs
from collections import defaultdict
import csv
from sqlalchemy import func, or_


# We import the tables
from models.sql_alchemy_models.artist_sql_model import Artist
from models.sql_alchemy_models.release_sql_model import Release
from models.sql_alchemy_models.track_sql_model import Track
from models.sql_alchemy_models.track_stream_sql_model import TrackStream
from models.sql_alchemy_models.spotify_track_sql_model import SpotifyTrack

from config import session


# We import the user ID of the only user we have in the database
from constants.service import USER_ID, RELEASE_TYPE


from collections import defaultdict
from sqlalchemy import func
import csv


def artists_data_to_csv(session, output_file="data/csv/artists_data.csv"):
    """
    Export aggregated stream and release statistics for all artists to a CSV file.

    Args:
        session: SQLAlchemy session object
        output_file: Path to the output CSV file
    """
    # Define the output columns
    fieldnames = [
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
    ]

    # Initialize stats with defaults for each artist
    stats = defaultdict(
        lambda: {
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
        }
    )

    # Aggregate stream data per artist (all artists)
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
        )
        .join(Artist.tracks)
        .join(Track.streams)
        .group_by(Artist.id)
    )

    for row in stream_q:
        stats[row.artist_id].update(
            {
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
            }
        )

    # Aggregate release counts per artist (all artists)
    release_q = (
        session.query(
            Artist.id.label("artist_id"),
            Release.release_type.label("release_type"),
            func.count(Release.id).label("count"),
        )
        .join(Release.artists)
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


def tracks_data_to_csv(session, output_file="data/csv/tracks_data.csv"):
    """
    Export aggregated stream statistics for all tracks to a CSV file.

    Args:
        session: SQLAlchemy session object
        output_file: Path to the output CSV file
    """
    # Define the output columns
    fieldnames = [
        "Name",
        "Duration_Ms",
        "First_Played_At",
        "Last_Played_At",
        "Track_Done_Count",
        "Skipped_Count",
        "Click_Row_Count",
        "Minutes_Streamed",
    ]

    # Initialize stats with defaults for each track
    stats = defaultdict(
        lambda: {
            "Name": None,
            "Duration_Ms": 0,
            "First_Played_At": 0,
            "Last_Played_At": 0,
            "Minutes_Streamed": 0,
            "Click_Row_Count": 0,
            "Skipped_Count": 0,
            "Track_Done_Count": 0,
        }
    )

    # Aggregate stream data per track (all tracks)
    stream_q = (
        session.query(
            Track.id.label("track_id"),
            Track.name,
            Track.duration_ms,
            func.sum(TrackStream.total_duration_play_s).label("minutes_streamed"),
            func.sum(TrackStream.click_row_count).label("click_count"),
            func.sum(TrackStream.skipped_count).label("skipped_count"),
            func.sum(TrackStream.track_done_count).label("track_done_count"),
        )
        .join(Track.streams)
        .group_by(Track.id)
    )

    for row in stream_q:
        stats[row.track_id].update(
            {
                "Name": row.name,
                "Duration_Ms": row.duration_ms,
                "Minutes_Streamed": row.minutes_streamed // 60 or 0,
                "Click_Row_Count": row.click_count or 0,
                "Skipped_Count": row.skipped_count or 0,
                "Track_Done_Count": row.track_done_count or 0,
            }
        )

    # Write out to CSV
    with open(output_file, "w", newline="", encoding="utf-8") as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        for data in stats.values():
            writer.writerow(data)

    print(f"Exported data for {len(stats)} track to {output_file}")


def releases_data_to_csv(session, output_file="data/csv/releases_data.csv"):
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
            func.sum(TrackStream.total_duration_play_s).label("minutes_streamed"),
            func.sum(TrackStream.click_row_count).label("click_count"),
            func.sum(TrackStream.skipped_count).label("skipped_count"),
            func.sum(TrackStream.track_done_count).label("track_done_count"),
        )
        .join(Release.spotify_tracks)
        .join(SpotifyTrack.canonical)
        .join(Track.streams)
        .filter(or_(Release.release_type == "album", Release.release_type == "ep"))
        .group_by(Release.id)
    )

    for row in stream_q:
        stats[row.release_id].update(
            {
                "Name": row.name or None,
                "Release_Type": row.release_type or None,
                "Popularity": row.popularity or 0,
                "Total_Duration_m": row.total_duration_ms // 60000 or 0,
                "Minutes_Streamed": row.minutes_streamed // 60 or 0,
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
