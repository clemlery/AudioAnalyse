"""dao/fetch_dao/artist_dao.py

Contains the Fetch DAO (Data Access Object) for all operations related to Spotify artists.
Each method corresponds to a Spotify API REST endpoint returning information about artists.
"""
from typing import Any, Dict, List, Optional, Set

from pydantic import ValidationError

from dao.base_dao import BaseFetchDAO
from models.data_class_models.artist import Artist
from models.data_class_models.artists import Artists
from constants.api import (
    SPOTIFY_ARTISTS_URL,
    SPOTIFY_TOP_ARTISTS_URL,
    SPOTIFY_FOLLOWED_ARTISTS_URL,
    SPOTIFY_CHECK_FOLLOWED_ARTISTS_URL_TEMPLATE,
)


class ArtistFetchDAO(BaseFetchDAO):
    """
    Data Access Object for Spotify artists.
    Groups methods to retrieve a single artist, multiple artists,
    user's top artists, and artist follow checks.
    """
    @staticmethod
    def fetch_artist(
        access_token: str,
        artist_id: str
    ) -> Artist:
        """Retrieve an artist by its ID.

        Keyword arguments:
        access_token -- a valid Spotify access token
        artist_id -- the ID of the artist to retrieve
        """
        data = ArtistFetchDAO._request(f"{SPOTIFY_ARTISTS_URL}/{artist_id}", access_token)
        return Artist.model_validate(data)
    
    @staticmethod
    def fetch_artists(
        access_token: str,
        artist_ids: List[str] | Set[str]
    ) -> List[Artist]:
        """Retrieve multiple artists by their IDs.

        Keyword arguments:
        access_token -- a valid Spotify access token
        artist_ids -- a list or set of artist IDs to retrieve
        """
        query = ",".join(artist_ids)
        data = ArtistFetchDAO._request(f"{SPOTIFY_ARTISTS_URL}?ids={query}", access_token)
        artists = []
        for item in data.get('artists', []):
            try:
                artist = Artist.model_validate(item)
                artists.append(artist)
            except ValidationError:
                continue
        return artists

    @staticmethod
    def fetch_top_artists(
        access_token: str,
        time_range: str = "medium_term",
        limit: int = 20
    ) -> Artists:
        """Retrieve the user's top artists for a specified time range.

        Keyword arguments:
        access_token -- a valid Spotify access token
        time_range -- time range for the top artists (default 'medium_term')
        limit -- number of top artists to retrieve (default 20)
        """
        params: Dict[str, Any] = {"time_range": time_range, "limit": limit}
        data = ArtistFetchDAO._request(SPOTIFY_TOP_ARTISTS_URL, access_token, params)
        return Artists.model_validate(data)
    
    @staticmethod
    def fetch_followed_artists(
        access_token: str,
        limit: int = 20,
        after: Optional[str] = None
    ) -> Artists:
        """Retrieve a paginated list of artists followed by the user.

        Keyword arguments:
        access_token -- a valid Spotify access token
        limit -- number of followed artists to retrieve (default 20)
        after -- cursor for pagination
        """
        params: Dict[str, Any] = {"type": "artist", "limit": limit}
        if after:
            params["after"] = after
        data = ArtistFetchDAO._request(SPOTIFY_FOLLOWED_ARTISTS_URL, access_token, params)
        return Artists.model_validate(data['artists'])

    @staticmethod
    def fetch_check_user_follows_artists(
        access_token: str,
        artist_ids: List[str]
    ) -> List[bool]:
        """Check if the user follows specified artists.

        Keyword arguments:
        access_token -- a valid Spotify access token
        artist_ids -- list of artist IDs to check
        """
        query = ",".join(artist_ids)
        SPOTIFY_ARTISTS_URL = f"{SPOTIFY_CHECK_FOLLOWED_ARTISTS_URL_TEMPLATE}&ids={query}"
        return ArtistFetchDAO._request(SPOTIFY_ARTISTS_URL, access_token)
