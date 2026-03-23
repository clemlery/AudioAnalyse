#!/usr/bin/env python3
"""
import_from_csv.py — Import tracks/albums/artists from SQLite dataset into the database.

Usage:
    python import_from_csv.py [sqlite_path] [limit]

Examples:
    python import_from_csv.py                                        # full import
    python import_from_csv.py data/dataset/extracted.sqlite          # explicit path
    python import_from_csv.py data/dataset/extracted.sqlite 500      # limit to 500 tracks
"""

import sys

# Force model registration before session is used
from models.orm.track_sql_model import Track
from models.orm.artist_sql_model import Artist
from models.orm.release_sql_model import Release
from models.orm.spotify_track_sql_model import SpotifyTrack
from models.orm.track_stream_sql_model import TrackStream
from models.orm.track_stream_day_sql_model import TrackStreamDay
from models.orm.metrics import ArtistMetricsSnapshot, TrackMetricsSnapshot
from models.orm.user_sql_model import User

from pipeline.dataset_importer import SqliteDatasetImporter

if __name__ == "__main__":
    sqlite_path = sys.argv[1] if len(sys.argv) > 1 else "data/dataset/extracted.sqlite"
    limit = int(sys.argv[2]) if len(sys.argv) > 2 else None

    print(f"SQLite : {sqlite_path}")
    if limit:
        print(f"Limit  : {limit} tracks")

    importer = SqliteDatasetImporter(sqlite_path)
    stats = importer.import_dataset(limit=limit)

    print("\n" + "=" * 60)
    print("IMPORT TERMINÉ")
    print("=" * 60)
    for key, value in stats.items():
        print(f"  {key:<30} {value}")
    print("=" * 60)
