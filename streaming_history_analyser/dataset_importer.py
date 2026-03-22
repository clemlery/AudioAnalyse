# dataset_importer.py — Import SQLite track dataset (~2M rows)

import sqlite3
import time
from typing import Optional

from config import session, logger
from models.sql_alchemy_models.artist_sql_model import Artist
from models.sql_alchemy_models.release_sql_model import Release
from models.sql_alchemy_models.spotify_track_sql_model import SpotifyTrack
from models.sql_alchemy_models.track_sql_model import Track
from models.sql_alchemy_models.association import release_artist, track_artist


COMMIT_EVERY = 2000


def _extract_id(uri: str) -> str:
    """Extract the Spotify ID from a URI like 'spotify:track:ID'."""
    return uri.split(":")[-1] if uri else ""


class SqliteDatasetImporter:
    """Import the SQLite dataset into the database (no Spotify API calls).

    Fields used from the 'extracted' table:
        track_uri, track_name, duration_ms,
        artist_name, artist_uri,
        album_name, album_uri

    Fields set to defaults (not available in the dataset):
        Artist.followers   → 0
        Artist.genres      → []
        Artist.image       → ""
        Release.release_type → "album"
        Release.image      → ""
        Release.release_date → "unknown"
        Release.total_tracks → 0
    """

    def __init__(self, sqlite_path: str):
        self.sqlite_path = sqlite_path
        self.stats = {
            "tracks_created": 0,
            "tracks_skipped": 0,
            "artists_created": 0,
            "releases_created": 0,
            "errors": 0,
        }
        self._artist_cache: dict[str, int] = {}
        self._release_cache: dict[str, int] = {}
        self._track_cache: set[str] = set()
        self._release_artist_cache: set[tuple] = set()

    # ------------------------------------------------------------------
    # Public entry point
    # ------------------------------------------------------------------

    def import_dataset(self, limit: Optional[int] = None) -> dict:
        """Import rows from the SQLite database. Returns stats dict."""
        logger.info(f"[sqlite_importer] Reading SQLite: {self.sqlite_path}")

        existing = session.query(SpotifyTrack.spotify_id).all()
        self._track_cache = {row[0] for row in existing}
        logger.info(f"[sqlite_importer] {len(self._track_cache)} tracks already in DB")

        processed = 0
        committed = 0
        t0 = time.perf_counter()

        conn = sqlite3.connect(self.sqlite_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute(
            "SELECT track_uri, track_name, artist_name, artist_uri, "
            "album_name, album_uri, duration_ms FROM extracted"
        )

        for row in cursor:
            spotify_track_id = _extract_id(row["track_uri"])
            if not spotify_track_id:
                continue

            if spotify_track_id in self._track_cache:
                self.stats["tracks_skipped"] += 1
                continue

            try:
                self._import_row(row, spotify_track_id)
                self._track_cache.add(spotify_track_id)
                processed += 1
            except Exception as e:
                logger.error(f"[sqlite_importer] Error on track {spotify_track_id}: {e}")
                session.rollback()
                self.stats["errors"] += 1
                continue

            if processed % COMMIT_EVERY == 0:
                session.commit()
                committed += processed
                elapsed = time.perf_counter() - t0
                logger.info(
                    f"[sqlite_importer] {committed} committed | "
                    f"tracks={self.stats['tracks_created']}, "
                    f"artists={self.stats['artists_created']}, "
                    f"releases={self.stats['releases_created']}, "
                    f"errors={self.stats['errors']} | "
                    f"{elapsed:.1f}s elapsed"
                )

            if limit and self.stats["tracks_created"] >= limit:
                break

        conn.close()

        session.commit()
        elapsed = time.perf_counter() - t0
        logger.info(
            f"[sqlite_importer] Done in {elapsed:.1f}s | "
            f"tracks={self.stats['tracks_created']}, "
            f"skipped={self.stats['tracks_skipped']}, "
            f"artists={self.stats['artists_created']}, "
            f"releases={self.stats['releases_created']}, "
            f"errors={self.stats['errors']}"
        )
        return self.stats

    # ------------------------------------------------------------------
    # Row processing
    # ------------------------------------------------------------------

    def _import_row(self, row: sqlite3.Row, spotify_track_id: str) -> None:
        track_name = row["track_name"] or "Unknown"
        duration_ms = row["duration_ms"] or 0
        artist_name = row["artist_name"] or "Unknown"
        artist_spotify_id = _extract_id(row["artist_uri"])
        album_name = row["album_name"] or "Unknown"
        release_spotify_id = _extract_id(row["album_uri"])

        artist_db_id = self._get_or_create_artist(artist_name, artist_spotify_id)
        release_db_id = self._get_or_create_release(album_name, release_spotify_id)
        self._link_release_artist(release_db_id, artist_db_id)

        track = Track(name=track_name, duration_ms=duration_ms)
        session.add(track)
        session.flush()
        self.stats["tracks_created"] += 1

        session.execute(
            track_artist.insert().values(track_id=track.id, artist_id=artist_db_id)
        )

        session.add(SpotifyTrack(
            track_id=track.id,
            spotify_id=spotify_track_id,
            release_id=release_db_id,
        ))
        session.flush()

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _get_or_create_artist(self, name: str, spotify_id: str) -> int:
        if spotify_id in self._artist_cache:
            return self._artist_cache[spotify_id]

        artist = session.query(Artist).filter(Artist.spotify_id == spotify_id).first()
        if not artist:
            artist = Artist(
                spotify_id=spotify_id,
                name=name,
                followers=0,
                popularity=None,
                genres=[],
                image="",
            )
            session.add(artist)
            session.flush()
            self.stats["artists_created"] += 1

        self._artist_cache[spotify_id] = artist.id
        return artist.id

    def _get_or_create_release(self, album_name: str, spotify_id: str) -> int:
        if spotify_id in self._release_cache:
            return self._release_cache[spotify_id]

        release = session.query(Release).filter(Release.spotify_id == spotify_id).first()
        if not release:
            release = Release(
                spotify_id=spotify_id,
                release_type="album",
                name=album_name,
                popularity=None,
                image="",
                release_date="unknown",
                total_tracks=0,
            )
            session.add(release)
            session.flush()
            self.stats["releases_created"] += 1

        self._release_cache[spotify_id] = release.id
        return release.id

    def _link_release_artist(self, release_id: int, artist_id: int) -> None:
        key = (release_id, artist_id)
        if key in self._release_artist_cache:
            return
        exists = session.query(release_artist).filter(
            (release_artist.c.release_id == release_id)
            & (release_artist.c.artist_id == artist_id)
        ).first()
        if not exists:
            session.execute(
                release_artist.insert().values(release_id=release_id, artist_id=artist_id)
            )
        self._release_artist_cache.add(key)
