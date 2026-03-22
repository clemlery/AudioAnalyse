# dataset_importer.py — Import 80k track dataset from CSV

import csv
import hashlib
import time
from typing import Optional

from config import session, logger
# Import all models to avoid circular dependency issues with SQLAlchemy
from models.sql_alchemy_models.artist_sql_model import Artist
from models.sql_alchemy_models.release_sql_model import Release
from models.sql_alchemy_models.spotify_track_sql_model import SpotifyTrack
from models.sql_alchemy_models.track_sql_model import Track
from models.sql_alchemy_models.association import release_artist, track_artist


COMMIT_EVERY = 500  # commit after N new spotify_tracks


def _hash_id(value: str) -> str:
    """Generate a deterministic 22-char hex ID from a string."""
    return hashlib.sha1(value.lower().encode()).hexdigest()[:22]


class CsvDatasetImporter:
    """Import CSV dataset directly into the database (no Spotify API calls).

    Fields used from CSV:
        track_id, track_name, duration_ms, artists (;-separated names), album_name, popularity

    Fields that can't be inferred from the CSV (set to defaults):
        Artist.spotify_id  → SHA1 hash of lowercased name
        Artist.followers   → 0
        Artist.genres      → []
        Artist.image       → ""
        Release.spotify_id → SHA1 hash of "album_name|first_artist"
        Release.release_type → "album"
        Release.image      → ""
        Release.release_date → "unknown"
        Release.total_tracks → 0
    """

    def __init__(self, csv_path: str):
        self.csv_path = csv_path
        self.stats = {
            "tracks_created": 0,
            "tracks_skipped": 0,
            "artists_created": 0,
            "releases_created": 0,
            "errors": 0,
        }
        # In-memory caches to avoid repeated DB lookups within a run
        self._artist_cache: dict[str, int] = {}   # spotify_id → db id
        self._release_cache: dict[str, int] = {}  # spotify_id → db id
        self._track_cache: set[str] = set()       # spotify_ids already in DB

    # ------------------------------------------------------------------
    # Public entry point
    # ------------------------------------------------------------------

    def import_dataset(self, limit: Optional[int] = None) -> dict:
        """Import CSV rows into the database. Returns stats dict."""
        logger.info(f"[csv_importer] Reading CSV: {self.csv_path}")

        # Pre-load existing SpotifyTrack spotify_ids to skip duplicates fast
        existing = session.query(SpotifyTrack.spotify_id).all()
        self._track_cache = {row[0] for row in existing}
        logger.info(f"[csv_importer] {len(self._track_cache)} tracks already in DB")

        processed = 0
        committed = 0

        t0 = time.perf_counter()
        with open(self.csv_path, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                spotify_track_id = row.get("track_id", "").strip()
                if not spotify_track_id:
                    continue

                if spotify_track_id in self._track_cache:
                    self.stats["tracks_skipped"] += 1
                    continue

                try:
                    self._import_row(row)
                    self._track_cache.add(spotify_track_id)
                    processed += 1
                except Exception as e:
                    logger.error(f"[csv_importer] Error on track {spotify_track_id}: {e}")
                    session.rollback()
                    self.stats["errors"] += 1
                    continue

                if processed % COMMIT_EVERY == 0:
                    session.commit()
                    committed += processed
                    elapsed = time.perf_counter() - t0
                    logger.info(
                        f"[csv_importer] {committed} committed | "
                        f"tracks={self.stats['tracks_created']}, "
                        f"artists={self.stats['artists_created']}, "
                        f"releases={self.stats['releases_created']}, "
                        f"errors={self.stats['errors']} | "
                        f"{elapsed:.1f}s elapsed"
                    )

                if limit and self.stats["tracks_created"] >= limit:
                    break

        # Final commit
        session.commit()
        elapsed = time.perf_counter() - t0
        logger.info(
            f"[csv_importer] Done in {elapsed:.1f}s | "
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

    def _import_row(self, row: dict) -> None:
        spotify_track_id = row["track_id"].strip()
        track_name = row.get("track_name", "").strip() or "Unknown"
        duration_ms = int(float(row.get("duration_ms", 0) or 0))
        artists_str = row.get("artists", "").strip()
        album_name = row.get("album_name", "").strip() or "Unknown"

        artist_names = [a.strip() for a in artists_str.split(";") if a.strip()]
        if not artist_names:
            artist_names = ["Unknown"]

        # --- Artists ---
        artist_db_ids = []
        for name in artist_names:
            db_id = self._get_or_create_artist(name)
            artist_db_ids.append(db_id)

        # --- Release (album) ---
        release_db_id = self._get_or_create_release(album_name, artist_names[0])

        # Link artists ↔ release
        for artist_db_id in artist_db_ids:
            self._link_release_artist(release_db_id, artist_db_id)

        # --- Track (canonical) ---
        track = Track(name=track_name, duration_ms=duration_ms)
        session.add(track)
        session.flush()
        self.stats["tracks_created"] += 1

        # Link artists ↔ track
        for artist_db_id in artist_db_ids:
            session.execute(
                track_artist.insert().values(
                    track_id=track.id, artist_id=artist_db_id
                )
            )

        # --- SpotifyTrack ---
        spotify_track = SpotifyTrack(
            track_id=track.id,
            spotify_id=spotify_track_id,
            release_id=release_db_id,
        )
        session.add(spotify_track)
        session.flush()

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _get_or_create_artist(self, name: str) -> int:
        artist_spotify_id = _hash_id(name)
        if artist_spotify_id in self._artist_cache:
            return self._artist_cache[artist_spotify_id]

        artist = session.query(Artist).filter(
            Artist.spotify_id == artist_spotify_id
        ).first()

        if not artist:
            artist = Artist(
                spotify_id=artist_spotify_id,
                name=name,
                followers=0,
                popularity=None,
                genres=[],
                image="",
            )
            session.add(artist)
            session.flush()
            self.stats["artists_created"] += 1

        self._artist_cache[artist_spotify_id] = artist.id
        return artist.id

    def _get_or_create_release(self, album_name: str, first_artist: str) -> int:
        release_spotify_id = _hash_id(f"{album_name}|{first_artist}")
        if release_spotify_id in self._release_cache:
            return self._release_cache[release_spotify_id]

        release = session.query(Release).filter(
            Release.spotify_id == release_spotify_id
        ).first()

        if not release:
            release = Release(
                spotify_id=release_spotify_id,
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

        self._release_cache[release_spotify_id] = release.id
        return release.id

    def _link_release_artist(self, release_id: int, artist_id: int) -> None:
        exists = session.query(release_artist).filter(
            (release_artist.c.release_id == release_id)
            & (release_artist.c.artist_id == artist_id)
        ).first()
        if not exists:
            session.execute(
                release_artist.insert().values(
                    release_id=release_id, artist_id=artist_id
                )
            )
