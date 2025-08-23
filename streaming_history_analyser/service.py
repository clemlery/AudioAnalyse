# service.py


from constants.scraping import (
    ARTIST_URI,
    ARTIST_URL,
    SPOTIFY_BASE_URL,
    TRACK_URI,
    TRACK_URL,
)
from constants.service import (
    RELEASE_TYPE,
    ALBUM_MIN_DURATION_MS,
    ALBUM_MIN_TRACK_NUMBER,
    EP_MIN_TRACK_NUMBER,
)
from datetime import datetime, timedelta, timezone
from typing import Tuple
from dao.db_dao.user_dao import UserDAO
from auth import ConfigAuth
from dao.service import BrowserManager, get_tokens
from dao.scrap_dao.spotify_artist_scraper_dao import SpotifyArtistScraperDAO
from dao.scrap_dao.spotify_track_scraper_dao import SpotifyTrackScraperDAO


def chunk_list(lst, size):
    """Yield successive chunks of given size from lst."""
    for i in range(0, len(lst), size):
        yield lst[i : i + size]


def total_duration_ms(tracks) -> int:
    return sum(track.duration_ms for track in tracks)


def define_release_type(release_data) -> RELEASE_TYPE:
    """Return SINGLE, EP or ALBUM based on the spotify rules"""
    track_number = len(release_data.tracks.items)
    release_duration_ms = total_duration_ms(release_data.tracks.items)
    if (
        release_duration_ms >= ALBUM_MIN_DURATION_MS
        or track_number >= ALBUM_MIN_TRACK_NUMBER
    ):
        return RELEASE_TYPE.ALBUM
    elif (
        track_number >= EP_MIN_TRACK_NUMBER
        and release_duration_ms <= ALBUM_MIN_DURATION_MS
    ):
        return RELEASE_TYPE.EP
    else:
        return RELEASE_TYPE.SINGLE


def verify_token(user):
    exp = user.updated_at + timedelta(seconds=user.expires_in)
    if datetime.now(timezone.utc) >= exp:
        tokens = ConfigAuth.refresh_token(user.refresh_token)
        UserDAO.update_user_access_token(
            user_id=user.id,
            access_token=tokens["access_token"],
            expires_in=tokens["expires_in"],
        )


def init_spotify_scraper_daos() -> Tuple[
    SpotifyArtistScraperDAO, SpotifyTrackScraperDAO
]:
    track_id = "5GT7fRtPrfhjJScixSFdZW"
    artist_id = "1JhiIIXT9DWqEU3BYFZwGA"

    bm = BrowserManager()
    bm.open_page(SPOTIFY_BASE_URL)
    bm.consent_cookies()
    bm.open_page(TRACK_URL + track_id)
    bm.open_page(ARTIST_URL + artist_id)
    logs = bm.get_cdp_log()
    track_client_token, access_token, track_hash_value = get_tokens(TRACK_URI, logs)
    artist_client_token, access_token, artist_hash_value = get_tokens(ARTIST_URI, logs)
    cookies = bm.get_cookies()
    user_agent = bm.get_user_agent()
    bm.quit_driver()

    track_scrap_dao = SpotifyTrackScraperDAO(
        access_token, track_client_token, user_agent, track_hash_value, cookies
    )
    artist_scrap_dao = SpotifyArtistScraperDAO(
        access_token, artist_client_token, user_agent, artist_hash_value, cookies
    )

    return (artist_scrap_dao, track_scrap_dao)
