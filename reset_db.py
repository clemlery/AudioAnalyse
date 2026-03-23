"""
Script to delete all data from the database except the 'user' table.
Deletion order respects foreign key constraints.
"""

from sqlalchemy import text
from core.config import session

TABLES_TO_DELETE = [
    "track_metrics_snapshot",
    "artist_metrics_snapshot",
    "track_stream_day",
    "track_stream",
    "track_artist",
    "release_artist",
    "spotify_track",
    "track",
    "artist",
    "release",
]

def reset_db():
    print("WARNING: This will permanently delete all data except the 'user' table.")
    confirm = input("Type 'yes' to confirm: ")
    if confirm.strip().lower() != "yes":
        print("Aborted.")
        return

    try:
        for table in TABLES_TO_DELETE:
            result = session.execute(text(f"DELETE FROM {table}"))
            print(f"  Deleted {result.rowcount} rows from '{table}'")

        session.commit()
        print("\nDatabase reset complete.")
    except Exception as e:
        session.rollback()
        print(f"\nError: {e}")
        raise

if __name__ == "__main__":
    reset_db()
