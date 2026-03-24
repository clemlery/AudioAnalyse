# dataset_importer.py — Import SQLite track dataset (~2M rows)

import sqlite3
import time
from typing import Optional

from core.config import session, logger
from models.orm.artist_sql_model import Artist
from models.orm.release_sql_model import Release
from models.orm.spotify_track_sql_model import SpotifyTrack
from models.orm.track_sql_model import Track
from models.orm.association import release_artist, track_artist


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
        # Committed caches — only contain IDs that have been committed to the DB
        self._artist_cache: dict[str, int] = {}
        self._release_cache: dict[str, int] = {}
        self._track_cache: set[str] = set()
        self._release_artist_cache: set[tuple] = set()

        # Pending since last commit — invalidated on rollback
        self._pending_artist_keys: set[str] = set()
        self._pending_release_keys: set[str] = set()
        self._pending_track_keys: set[str] = set()
        self._pending_release_artist_keys: set[tuple] = set()
        self._pending_stats: dict[str, int] = {
            "tracks_created": 0,
            "artists_created": 0,
            "releases_created": 0,
        }

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
                processed += 1
            except Exception as e:
                logger.error(f"[sqlite_importer] Error on track {spotify_track_id}: {e}")
                session.rollback()
                self._on_rollback()
                self.stats["errors"] += 1
                continue

            if processed % COMMIT_EVERY == 0:
                session.commit()
                self._on_commit()
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
        self._on_commit()
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
    # Commit / rollback cache management
    # ------------------------------------------------------------------

    def _on_commit(self) -> None:
        """Called after session.commit() — promote pending entries to committed state."""
        self._pending_artist_keys.clear()
        self._pending_release_keys.clear()
        self._pending_track_keys.clear()
        self._pending_release_artist_keys.clear()
        self._pending_stats = {"tracks_created": 0, "artists_created": 0, "releases_created": 0}

    def _on_rollback(self) -> None:
        """Called after session.rollback() — purge stale pending entries from caches."""
        for key in self._pending_artist_keys:
            self._artist_cache.pop(key, None)
        for key in self._pending_release_keys:
            self._release_cache.pop(key, None)
        for key in self._pending_track_keys:
            self._track_cache.discard(key)
        for key in self._pending_release_artist_keys:
            self._release_artist_cache.discard(key)

        self.stats["tracks_created"] -= self._pending_stats["tracks_created"]
        self.stats["artists_created"] -= self._pending_stats["artists_created"]
        self.stats["releases_created"] -= self._pending_stats["releases_created"]

        self._pending_artist_keys.clear()
        self._pending_release_keys.clear()
        self._pending_track_keys.clear()
        self._pending_release_artist_keys.clear()
        self._pending_stats = {"tracks_created": 0, "artists_created": 0, "releases_created": 0}

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

        session.execute(
            track_artist.insert().values(track_id=track.id, artist_id=artist_db_id)
        )

        session.add(SpotifyTrack(
            track_id=track.id,
            spotify_id=spotify_track_id,
            release_id=release_db_id,
        ))
        session.flush()

        # Track only after all flushes succeed
        self._track_cache.add(spotify_track_id)
        self._pending_track_keys.add(spotify_track_id)
        self.stats["tracks_created"] += 1
        self._pending_stats["tracks_created"] += 1

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
                name=name[:255],
                followers=0,
                popularity=None,
                genres=[],
                image="",
            )
            session.add(artist)
            session.flush()
            self.stats["artists_created"] += 1
            self._pending_stats["artists_created"] += 1
            self._pending_artist_keys.add(spotify_id)

        self._artist_cache[spotify_id] = artist.id
        # If the artist already existed in DB (not newly created), it's already committed
        # so we don't add it to pending — it will survive any rollback.
        return artist.id

    def _get_or_create_release(self, album_name: str, spotify_id: str) -> int:
        if spotify_id in self._release_cache:
            return self._release_cache[spotify_id]

        release = session.query(Release).filter(Release.spotify_id == spotify_id).first()
        if not release:
            release = Release(
                spotify_id=spotify_id,
                release_type="album",
                name=album_name[:255],
                popularity=None,
                image="",
                release_date="unknown",
                total_tracks=0,
            )
            session.add(release)
            session.flush()
            self.stats["releases_created"] += 1
            self._pending_stats["releases_created"] += 1
            self._pending_release_keys.add(spotify_id)

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
        self._pending_release_artist_keys.add(key)
