# process.py

from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, field
from typing import Any, Dict, Optional, Tuple
from auth import ConfigAuth
from constants.service import RELEASE_TYPE

# We import all the Fetch DAOs
from dao.db_dao.track_stream_day_dao import TrackStreamDayDAO
from dao.fetch_dao.track_fetch_dao import TrackFetchDAO
from dao.fetch_dao.artist_fetch_dao import ArtistFetchDAO
from dao.fetch_dao.album_fetch_dao import AlbumFetchDAO
from dao.fetch_dao.user_fetch_dao import UserFetchDao

# We import all the DB DAOs
from dao.db_dao.track_stream_dao import TrackStreamDAO
from dao.db_dao.artist_dao import ArtistDAO
from dao.db_dao.release_dao import ReleaseDAO
from dao.db_dao.track_dao import TrackDAO
from dao.db_dao.spotify_track_dao import SpotifyTrackDAO
from dao.db_dao.user_dao import UserDAO
from dao.db_dao.metrics_dao import TrackMetricsSnapshotDAO, ArtistMetricsSnapshotDAO

# We import all the scrap DAOs
from dao.scrap_dao.spotify_artist_scraper_dao import SpotifyArtistScraperDAO
from dao.scrap_dao.spotify_track_scraper_dao import SpotifyTrackScraperDAO

# We import the association table
from models.data_class_models.album import Album
from models.sql_alchemy_models.association import track_artist, release_artist

# We import the logger global variable
from config import logger

# Other imports
from config import session
from sqlalchemy import select
from models.data_class_models.track import Track
from streaming_history_analyser.factory import BrowserTokenSource, ScraperFactory
from streaming_history_analyser.service import (
    chunk_list,
    define_release_type,
    verify_token,
)
from datetime import date, datetime
import time


@dataclass
class IngestContext:
    """Holds per-user mutable state across streaming history file batches.

    A single instance must be created per user before iterating over files,
    so that loop streaks are preserved across file boundaries.
    """

    user_id: str
    last_track_played: str = ""
    last_date: date = field(default_factory=lambda: datetime(1, 1, 1).date())
    loop_streak: int = 1
    loop_streak_day: int = 1


def _filter_new_track_ids(records):
    """Return set of Spotify track IDs not in local DB."""
    candidate_ids = set()
    for item in records:
        uri = item.get("spotify_track_uri")
        try:
            _, data_type, tid = uri.split(":")
            if data_type == "track":
                candidate_ids.add(tid)
        except Exception:
            logger.error(f"Invalid URI or error: {uri}")
    if not candidate_ids:
        return set()
    existing = SpotifyTrackDAO.get_existing_spotify_ids(list(candidate_ids))
    return candidate_ids - existing


def _fetch_all_tracks(token, ids, batch_size=50):
    """Fetch track objects in sub-batches."""
    tracks: list[Track] = []
    for chunk in chunk_list(list(ids), batch_size):
        tracks.extend(TrackFetchDAO.fetch_tracks(token, chunk))
    return tracks


# ----------------------- Process functions -----------------------


def _process_artists(
    new_artists: set[str],
    seen_artists: set[str],
    artist_scraper: SpotifyArtistScraperDAO | None,
    token: str,
    batch_size=50,
    max_workers=10,
):
    # Fetch all artist data from Spotify API
    all_artists = []
    for chunk in chunk_list(list(new_artists), batch_size):
        all_artists.extend(ArtistFetchDAO.fetch_artists(token, chunk))

    # Parallelize scraping HTTP calls (skipped when artist_scraper is None)
    monthly_listeners_map: dict[str, int | None] = {}
    if artist_scraper is not None:
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = {
                executor.submit(artist_scraper.get_artist_monthly_listeners, art.id): art
                for art in all_artists
            }
            for future in as_completed(futures):
                art = futures[future]
                monthly_listeners_map[art.id] = future.result()

    # Sequential DB writes
    for art in all_artists:
        artist_obj = ArtistDAO.add_artist(art)
        ArtistMetricsSnapshotDAO.add_artist_metrics(
            artist_obj.id, monthly_listeners_map.get(art.id)
        )
        seen_artists.add(art.id)


def _process_releases(
    new_releases: set[str], seen_releases: set[str], token: str, batch_size=20
):
    # Fetch missing release data in batches of 20
    releases = []
    for chunk in chunk_list(list(new_releases), batch_size):
        releases.extend(AlbumFetchDAO.fetch_albums(token, chunk))

    # We add all the missing releases to the database
    for rel in releases:
        rel_type = (
            define_release_type(rel)
            if rel.album_type != "compilation"
            else RELEASE_TYPE.COMPILATION
        )
        ReleaseDAO.add_release(rel, rel_type.value)
        seen_releases.add(rel.id)


def _process_tracks(
    tracks: list[Track],
    track_scraper: SpotifyTrackScraperDAO | None,
    seen_spotify_tracks: set[str],
    max_workers=10,
):
    # Parallelize scraping HTTP calls (skipped when track_scraper is None)
    playcount_map: dict[str, int | None] = {}
    if track_scraper is not None:
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = {
                executor.submit(track_scraper.get_track_playcount, t.id): t
                for t in tracks
            }
            for future in as_completed(futures):
                t = futures[future]
                playcount_map[t.id] = future.result()

    # Sequential DB writes
    for t in tracks:
        seen_spotify_tracks.add(t.id)
        track_obj = TrackDAO.get_track_by_nd(
            t.name, t.duration_ms
        ) or TrackDAO.add_track(t)

        TrackMetricsSnapshotDAO.add_track_metrics(track_obj.id, playcount_map.get(t.id))

        if not SpotifyTrackDAO.get_spotify_track_by_spotify_id(t.id):
            SpotifyTrackDAO.add_spotify_track(
                t.id, track_obj.id, ReleaseDAO.get_release_by_spotify_id(t.album.id).id
            )
            seen_spotify_tracks.add(t.id)


def _associate_rows(tracks):
    # Link track<->artist and release<->artist
    for t in tracks:
        track_obj = TrackDAO.get_track_by_nd(t.name, t.duration_ms)
        rel_obj = ReleaseDAO.get_release_by_spotify_id(t.album.id)
        for a in t.artists:
            art_obj = ArtistDAO.get_artist_by_spotify_id(a.id)
            # Track-Artist
            if not session.execute(
                select(track_artist).where(
                    (track_artist.c.track_id == track_obj.id)
                    & (track_artist.c.artist_id == art_obj.id)
                )
            ).first():
                track_obj.artists.append(art_obj)
            # Release-Artist
            if not session.execute(
                select(release_artist).where(
                    (release_artist.c.release_id == rel_obj.id)
                    & (release_artist.c.artist_id == art_obj.id)
                )
            ).first():
                rel_obj.artists.append(art_obj)
        session.flush()


def _parse_record(raw: Dict[str, Any]) -> dict | None:
    """Normalize one raw record into a compact dict expected by downstream helpers."""
    ts = raw.get("ts")
    # Datetime parsing: accept ISO or "%Y-%m-%d %H:%M:%S" like strings
    dt = _parse_datetime(ts)
    id = raw.get("spotify_track_uri", None)
    if id == None:
        return None
    else:
        return {
            "done": raw.get("reason_end") == "trackdone",
            "skip": bool(raw.get("skipped")),
            "click": raw.get("reason_start") == "clickrow",
            "name": raw.get("master_metadata_track_name"),
            "artist": raw.get("master_metadata_album_artist_name"),
            "id": id.split(":")[2],
            "ms_played": int(raw.get("ms_played") or 0),
            "datetime": dt,
            "date": (dt.date() if isinstance(dt, datetime) else None),
        }


def _parse_datetime(value: str) -> Optional[datetime]:
    """Parse timestamps of the form 'YYYY-MM-DDTHH:MM:SSZ' (always same format)."""
    if not value:
        return None
    try:
        # Exemple : "2023-01-18T15:25:09Z"
        clean = value.replace("Z", "")
        return datetime.strptime(clean, "%Y-%m-%dT%H:%M:%S")
    except Exception as e:
        logger.error(f"Failed to parse datetime {value!r}: {e}")
        return None


def _resolve_track_obj(track_id: str, cache: dict | None = None):
    """Resolve DB Track object from a record's Spotify URI via SpotifyTrackDAO -> TrackDAO."""
    if cache is not None and track_id in cache:
        return cache[track_id]
    sp = SpotifyTrackDAO.get_spotify_track_by_spotify_id(track_id)
    result = TrackDAO.get_track_by_id(sp.track_id) if sp else None
    if cache is not None:
        cache[track_id] = result
    return result


def _update_loop_streaks(
    ctx: IngestContext, track_id: Optional[str], day: Optional[date]
) -> Tuple[int, int]:
    """
    Update loop streaks on ctx according to the current record.
    Returns (loop_streak, loop_streak_day).
    """
    # Streak per track
    if track_id and track_id == ctx.last_track_played:
        ctx.loop_streak += 1
    else:
        ctx.loop_streak = 1
        ctx.last_track_played = track_id or ""

    # Streak per day
    if day and day == ctx.last_date:
        ctx.loop_streak_day += 1
    else:
        ctx.loop_streak_day = 1
        ctx.last_date = day or ctx.last_date

    return ctx.loop_streak, ctx.loop_streak_day


def _persist_stream(track_id: int, user_id: int, meta: dict) -> None:
    """Insert one TrackStream row."""
    TrackStreamDAO.add_or_update_stream_track(
        track_id,
        user_id,
        meta["done"],
        meta["skip"],
        meta["click"],
        meta["loop_streak"],
        meta["datetime"],
        meta["duration_ms"],
    )


def _persist_stream_day(track_id: int, user_id: int, meta: dict) -> None:
    """Insert/update one TrackStreamDay row."""
    TrackStreamDayDAO.add_or_update_stream_track_day(
        track_id,
        user_id,
        meta["done"],
        meta["skip"],
        meta["click"],
        meta["loop_streak_day"],
        meta["date"],
        meta["duration_ms"],
    )


# ----------------------- Refactored main function -----------------------


def _process_stream_batch(records, ctx: IngestContext):
    """Insert or update stream records from a history batch."""
    # Pre-build the full spotify_id → Track cache with two bulk queries
    all_spotify_ids = set()
    for raw in records:
        uri = raw.get("spotify_track_uri")
        if uri:
            parts = uri.split(":")
            if len(parts) == 3 and parts[1] == "track":
                all_spotify_ids.add(parts[2])

    sp_map = SpotifyTrackDAO.get_spotify_tracks_bulk(list(all_spotify_ids))
    track_obj_map = TrackDAO.get_tracks_by_ids([sp.track_id for sp in sp_map.values()])
    cache: dict = {
        spotify_id: track_obj_map.get(sp.track_id)
        for spotify_id, sp in sp_map.items()
    }

    for raw in records:
        rec = _parse_record(raw)
        if rec is None:
            continue

        track = _resolve_track_obj(rec["id"], cache)
        if track is None:
            logger.warning(
                f"Unknown Spotify track in DB for ID={rec['id']!r}, name={rec['name']!r}"
            )
            continue

        loop_streak, loop_streak_day = _update_loop_streaks(ctx, rec["id"], rec["date"])

        meta = {
            "done": rec["done"],
            "skip": rec["skip"],
            "click": rec["click"],
            "loop_streak": loop_streak,
            "loop_streak_day": loop_streak_day,
            "date": rec["date"],
            "datetime": rec["datetime"],
            "duration_ms": track.duration_ms,
        }

        try:
            _persist_stream(track.id, ctx.user_id, meta)
            _persist_stream_day(track.id, ctx.user_id, meta)
        except Exception as e:
            logger.exception(f"Failed to persist stream for track_id={track.id}: {e}")
            # continue with others rather than aborting the batch


def exploit_streaming_history(
    streaming_history: list[dict],
    ctx: IngestContext,
    scraper_factory: ScraperFactory | None = None,
    scrape: bool = True,
) -> dict[str, float]:
    if scrape:
        if scraper_factory is None:
            scraper_factory = ScraperFactory(BrowserTokenSource())
        artist_scraper = scraper_factory.artist()
        track_scraper = scraper_factory.track()
    else:
        artist_scraper = None
        track_scraper = None

    new_auth = ConfigAuth()
    token = new_auth.access_token

    if not streaming_history:
        raise ValueError(
            "Streaming history file was not provided in exploit_streaming_history function"
        )

    seen_artists: set[str] = set()
    seen_releases: set[str] = set()
    seen_spotify_tracks: set[str] = set()
    timings: dict[str, float] = {}

    t0 = time.perf_counter()
    track_ids = _filter_new_track_ids(streaming_history)
    timings["filter_new_track_ids"] = time.perf_counter() - t0

    if track_ids:
        t0 = time.perf_counter()
        tracks = _fetch_all_tracks(token, track_ids)
        timings["fetch_all_tracks"] = time.perf_counter() - t0

        new_releases = {
            t.album.id
            for t in tracks
            if t.album.id not in seen_releases
            and not ReleaseDAO.get_release_by_spotify_id(t.album.id)
        }
        new_artists = {
            a.id
            for t in tracks
            for a in t.artists
            if a.id not in seen_artists and not ArtistDAO.get_artist_by_spotify_id(a.id)
        }

        t0 = time.perf_counter()
        _process_artists(new_artists, seen_artists, artist_scraper, token)
        timings["process_artists"] = time.perf_counter() - t0

        t0 = time.perf_counter()
        _process_releases(new_releases, seen_releases, token)
        timings["process_releases"] = time.perf_counter() - t0

        t0 = time.perf_counter()
        _process_tracks(tracks, track_scraper, seen_spotify_tracks)
        timings["process_tracks"] = time.perf_counter() - t0

        t0 = time.perf_counter()
        _associate_rows(tracks)
        timings["associate_rows"] = time.perf_counter() - t0

    t0 = time.perf_counter()
    _process_stream_batch(streaming_history, ctx)
    timings["process_stream_batch"] = time.perf_counter() - t0

    t0 = time.perf_counter()
    session.commit()
    session.expunge_all()
    timings["db_commit"] = time.perf_counter() - t0

    total = sum(timings.values())
    logger.info("Algorithm completed successfully — timings:")
    for phase, elapsed in timings.items():
        logger.info(f"  {phase:<30} {elapsed:6.2f}s  ({elapsed/total*100:.1f}%)")
    logger.info(f"  {'TOTAL':<30} {total:6.2f}s")

    return timings
