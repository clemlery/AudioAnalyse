#!/usr/bin/env python3
"""
test_dataset_import.py — Test dataset importer on small subset

Usage:
    python test_dataset_import.py <access_token> [csv_path] [num_tracks]

Example:
    python test_dataset_import.py "BQDx..." ./data/dataset/dataset.csv 100
"""

import sys

# Force import of all models before using session
from models.sql_alchemy_models.track_sql_model import Track
from models.sql_alchemy_models.artist_sql_model import Artist
from models.sql_alchemy_models.release_sql_model import Release
from models.sql_alchemy_models.spotify_track_sql_model import SpotifyTrack
from models.sql_alchemy_models.track_stream_sql_model import TrackStream

from streaming_history_analyser.dataset_importer import DatasetImporter

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)

    access_token = sys.argv[1]
    csv_path = sys.argv[2] if len(sys.argv) > 2 else "./data/dataset/dataset.csv"
    num_tracks = int(sys.argv[3]) if len(sys.argv) > 3 else 100

    print(f"[test] Using CSV: {csv_path}")
    print(f"[test] Limiting to {num_tracks} unique tracks")

    # Run import with limit
    importer = DatasetImporter(access_token, csv_path)
    print(f"[test] Starting import (DRY RUN = False)...")
    stats = importer.import_dataset(dry_run=False, limit=num_tracks)

    # Print stats
    print("\n" + "="*60)
    print("IMPORT COMPLETE")
    print("="*60)
    for key, value in stats.items():
        print(f"{key:.<40} {value}")
    print("="*60)
