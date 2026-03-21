# scrape.py — standalone metrics scraping job
# Scrapes monthly listeners and playcounts for all artists/tracks
# that have no snapshot yet. Designed to run after import.

import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Callable

from sqlalchemy import exists

from config import logger, session
from dao.db_dao.metrics_dao import ArtistMetricsSnapshotDAO, TrackMetricsSnapshotDAO
from models.sql_alchemy_models.artist_sql_model import Artist
from models.sql_alchemy_models.metrics import ArtistMetricsSnapshot, TrackMetricsSnapshot
from models.sql_alchemy_models.spotify_track_sql_model import SpotifyTrack
from streaming_history_analyser.factory import BrowserTokenSource, ScraperFactory


def _artists_without_metrics() -> list[Artist]:
    return (
        session.query(Artist)
        .filter(
            ~exists().where(ArtistMetricsSnapshot.artist_id == Artist.id)
        )
        .all()
    )


def _spotify_tracks_without_metrics() -> list[SpotifyTrack]:
    return (
        session.query(SpotifyTrack)
        .filter(
            ~exists().where(TrackMetricsSnapshot.track_id == SpotifyTrack.track_id)
        )
        .all()
    )


def run_metrics_scraping(
    scraper_factory: ScraperFactory | None = None,
    progress_callback: Callable[[str, int, int], None] | None = None,
    max_workers: int = 10,
) -> dict[str, float]:
    """Scrape monthly listeners and playcounts for all unscraped artists/tracks.

    Args:
        scraper_factory: if None, a BrowserTokenSource is created automatically.
        progress_callback: optional callable(message, done, total) for live progress.
        max_workers: thread pool size for parallel HTTP calls.

    Returns:
        dict of phase timings in seconds.
    """
    if scraper_factory is None:
        scraper_factory = ScraperFactory(BrowserTokenSource())

    artist_scraper = scraper_factory.artist()
    track_scraper = scraper_factory.track()
    timings: dict[str, float] = {}

    # ── Artists ──────────────────────────────────────────────────────────────
    t0 = time.perf_counter()
    artists = _artists_without_metrics()
    timings["query_artists"] = time.perf_counter() - t0
    logger.info(f"[scrape] {len(artists)} artists without metrics snapshot")

    if artists:
        t0 = time.perf_counter()
        monthly_listeners_map: dict[int, int | None] = {}

        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = {
                executor.submit(artist_scraper.get_artist_monthly_listeners, a.spotify_id): a
                for a in artists
            }
            done_count = 0
            for future in as_completed(futures):
                a = futures[future]
                monthly_listeners_map[a.id] = future.result()
                done_count += 1
                if progress_callback:
                    progress_callback(
                        f"Artists: {a.name}", done_count, len(artists)
                    )

        for a in artists:
            ArtistMetricsSnapshotDAO.add_artist_metrics(
                a.id, monthly_listeners_map.get(a.id)
            )

        session.flush()
        timings["scrape_artists"] = time.perf_counter() - t0
        logger.info(f"[scrape] artists done in {timings['scrape_artists']:.2f}s")

    # ── Tracks ───────────────────────────────────────────────────────────────
    t0 = time.perf_counter()
    sp_tracks = _spotify_tracks_without_metrics()
    timings["query_tracks"] = time.perf_counter() - t0
    logger.info(f"[scrape] {len(sp_tracks)} tracks without metrics snapshot")

    if sp_tracks:
        t0 = time.perf_counter()
        playcount_map: dict[int, int | None] = {}

        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = {
                executor.submit(track_scraper.get_track_playcount, sp.spotify_id): sp
                for sp in sp_tracks
            }
            done_count = 0
            for future in as_completed(futures):
                sp = futures[future]
                playcount_map[sp.track_id] = future.result()
                done_count += 1
                if progress_callback:
                    progress_callback(
                        f"Tracks: {done_count}/{len(sp_tracks)}", done_count, len(sp_tracks)
                    )

        for sp in sp_tracks:
            TrackMetricsSnapshotDAO.add_track_metrics(
                sp.track_id, playcount_map.get(sp.track_id)
            )

        session.flush()
        timings["scrape_tracks"] = time.perf_counter() - t0
        logger.info(f"[scrape] tracks done in {timings['scrape_tracks']:.2f}s")

    t0 = time.perf_counter()
    session.commit()
    timings["db_commit"] = time.perf_counter() - t0

    total = sum(timings.values())
    logger.info(f"[scrape] completed in {total:.2f}s")
    return timings
