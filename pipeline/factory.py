"""
factory.py — Provides a Factory and a Token Source for Spotify scraping DAOs.

Goal:
- Isolate token/cookies/user-agent retrieval (via BrowserManager) from business logic.
- Allow injecting a factory into process.py to construct DAOs without knowing init details.
- Be easy to test: you can provide a fake TokenSource in tests.

Main exports:
- ScraperContext (dataclass)
- TokenSource (Protocol)
- BrowserTokenSource (real implementation, with in-memory cache + optional TTL)
- StaticTokenSource (useful for tests)
- ScraperFactory (returns SpotifyArtistScraperDAO / SpotifyTrackScraperDAO)
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Protocol, Optional

from config import logger
from constants.scraping import (
    ARTIST_URI,
    ARTIST_URL,
    SPOTIFY_BASE_URL,
    TRACK_URI,
    TRACK_URL,
)
from dao.service import BrowserManager, get_tokens
from dao.scrap_dao.spotify_artist_scraper_dao import SpotifyArtistScraperDAO
from dao.scrap_dao.spotify_track_scraper_dao import SpotifyTrackScraperDAO


# =============================
# Data required by the DAOs
# =============================


@dataclass
class ScraperContext:
    access_token: str
    artist_client_token: str
    artist_hash: str
    track_client_token: str
    track_hash: str
    cookies: list[dict]
    user_agent: str
    # Optional: expiration date (if you want to invalidate the cache after some delay)
    expires_at: Optional[datetime] = None

    def __str__(self):
        def shorten(value: str, length: int = 9) -> str:
            if not value:
                return "None"
            return value[:length] + "..." if len(value) > length else value

        return (
            f"ScraperContext(\n"
            f"  access_token={self.access_token},\n"
            f"  artist_client_token={self.artist_client_token},\n"
            f"  artist_hash={self.artist_hash},\n"
            f"  track_client_token={self.track_client_token},\n"
            f"  track_hash={self.track_hash},\n"
            f"  cookies={' , '.join([f'{key}:{value}' for d in self.cookies for key, value in d.items()])},\n"
            f"  user_agent='{self.user_agent}',\n"
            f"  expires_at={self.expires_at}\n"
            f")"
        )


# =============================
# Token source abstraction
# =============================


class TokenSource(Protocol):
    """Minimal contract to obtain a ScraperContext."""

    def get_context(self) -> ScraperContext: ...


# ======================================================
# Real implementation: via Browser (CDP logs + cookies)
# ======================================================


class BrowserTokenSource:
    """
    Retrieves tokens/cookies/user-agent via BrowserManager and keeps an in-memory cache.

    - On first request, launches the browser, gathers data and builds a ScraperContext.
    - Afterwards, returns the cached context until expiration (TTL) if configured.
    """

    def __init__(self, *, ttl: Optional[timedelta] = timedelta(hours=1)) -> None:
        self._ctx: Optional[ScraperContext] = None
        self._ttl = ttl

    # “Sentinel” IDs to trigger relevant endpoints (keep public, stable IDs)
    _SAMPLE_TRACK_ID = (
        "7BKLCZ1jbUBVqRi2FVlTVw"  # "Closer" from Chainsmokers feat. Halsey
    )
    _SAMPLE_ARTIST_ID = "6qqNVTkY8uBg9cP3Jd7DAH"  # Billie Eilish

    def _fresh_context(self) -> ScraperContext:
        bm = BrowserManager()
        try:
            logger.debug("[BrowserTokenSource] Opening browser and initial navigation…")
            bm.open_page(SPOTIFY_BASE_URL)
            bm.consent_cookies()

            # Visit a track and an artist page to capture relevant requests
            bm.open_page(TRACK_URL + self._SAMPLE_TRACK_ID)
            bm.open_page(ARTIST_URL + self._SAMPLE_ARTIST_ID)

            logs = bm.get_cdp_log()
            # Extract tokens/hashes for track and artist
            track_client_token, access_token, track_hash_value = get_tokens(
                TRACK_URI, logs
            )
            artist_client_token, access_token, artist_hash_value = get_tokens(
                ARTIST_URI, logs
            )

            cookies = bm.get_cookies()
            user_agent = bm.get_user_agent()

            expires_at = None
            if self._ttl is not None:
                expires_at = datetime.now(tz=timezone.utc) + self._ttl

            ctx = ScraperContext(
                access_token=access_token,
                artist_client_token=artist_client_token,
                artist_hash=artist_hash_value,
                track_client_token=track_client_token,
                track_hash=track_hash_value,
                cookies=cookies,
                user_agent=user_agent,
                expires_at=expires_at,
            )
            logger.info("[BrowserTokenSource] Scraping context successfully generated.")
            return ctx
        finally:
            # Always close the browser, even on error
            try:
                bm.quit_driver()
            except Exception as e:
                logger.warning(f"[BrowserTokenSource] Failed to close browser: {e}")

    def _expired(self, ctx: ScraperContext) -> bool:
        if ctx.expires_at is None:
            return False
        # Compare in UTC
        now = datetime.now(tz=timezone.utc)
        return now >= ctx.expires_at

    def get_context(self) -> ScraperContext:
        if self._ctx is None:
            self._ctx = self._fresh_context()
            return self._ctx

        # If TTL is used and context expired, refresh it
        if self._expired(self._ctx):
            logger.info("[BrowserTokenSource] Context expired, regenerating…")
            self._ctx = self._fresh_context()

        return self._ctx


# =============================
# Scraping DAO factory
# =============================


class ScraperFactory:
    """
    Factory for Spotify scraper DAOs (artist/track) backed by a TokenSource.

    Typical usage in process.py:

        factory = ScraperFactory(BrowserTokenSource())
        artist_scraper = factory.artist()
        track_scraper = factory.track()
    """

    def __init__(self, token_source: TokenSource) -> None:
        self._token_source = token_source
        # Optional: cache instances if you want to reuse the same DAO
        self._artist_dao: Optional[SpotifyArtistScraperDAO] = None
        self._track_dao: Optional[SpotifyTrackScraperDAO] = None

    def artist(self) -> SpotifyArtistScraperDAO:
        if self._artist_dao is None:
            ctx = self._token_source.get_context()
            self._artist_dao = SpotifyArtistScraperDAO(
                ctx.access_token,
                ctx.artist_client_token,
                ctx.user_agent,
                ctx.artist_hash,
                ctx.cookies,
            )
        return self._artist_dao

    def track(self) -> SpotifyTrackScraperDAO:
        if self._track_dao is None:
            ctx = self._token_source.get_context()
            self._track_dao = SpotifyTrackScraperDAO(
                ctx.access_token,
                ctx.track_client_token,
                ctx.user_agent,
                ctx.track_hash,
                ctx.cookies,
            )
        return self._track_dao
