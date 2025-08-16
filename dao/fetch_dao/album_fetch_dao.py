"""dao/fetch_dao/album_fetch_dao.py

Contains the Fetch DAO (Data Access Object) for all operations related to Spotify albums.
Each method corresponds to a Spotify API REST endpoint returning albums or their tracks.
"""
from typing import Any, Dict, List, Set

from pydantic import ValidationError

from models.data_class_models.album import Album
from models.data_class_models.tracks import Tracks
from models.data_class_models.albums import Albums

from dao.base_dao import BaseFetchDAO

from constants.api import (
    SPOTIFY_ALBUMS_URL,
    SPOTIFY_ALBUM_TRACKS_URL_TEMPLATE,
    SPOTIFY_SAVED_ALBUMS_URL,
    SPOTIFY_CHECK_SAVED_ALBUMS_URL,
)


class AlbumFetchDAO(BaseFetchDAO):
    """
    Data Access Object for Spotify albums.
    Groups methods to retrieve an album, multiple albums,
    tracks of an album, saved albums, and saved album checks.
    """

    @staticmethod
    def fetch_album(
        access_token: str,
        album_id: str
    ) -> Album:
        """Retrieve a single album by its ID.

        Keyword arguments:
        access_token -- a valid Spotify access token
        album_id -- the ID of the album to retrieve
        """

        data = AlbumFetchDAO._request(f"{SPOTIFY_ALBUMS_URL}/{album_id}", access_token)
        return Album.model_validate(data)

    @staticmethod
    def fetch_albums(
        access_token: str,
        album_ids: List[str] | Set[str]
    ) -> List[Album]:
        """Retrieve multiple albums by their IDs.

        Keyword arguments:
        access_token -- a valid Spotify access token
        album_ids -- a list or set of album IDs to retrieve
        """
        query = ",".join(album_ids)
        data = AlbumFetchDAO._request(f"{SPOTIFY_ALBUMS_URL}?ids={query}", access_token)
        releases = []
        for item in data.get('albums', []):
            try:
                release = Album.model_validate(item)
                releases.append(release)
            except ValidationError:
                continue
        return releases

    @staticmethod
    def fetch_album_tracks(
        access_token: str,
        album_id: str,
        limit: int = 20,
        offset: int = 0
    ) -> Tracks:
        """Retrieve the tracks of a given album.

        Keyword arguments:
        access_token -- a valid Spotify access token
        album_id -- the ID of the album to retrieve tracks from
        limit -- number of tracks to retrieve (default 20)
        offset -- offset for pagination (default 0)
        """
        params: Dict[str, Any] = {"limit": limit, "offset": offset}
        SPOTIFY_ALBUMS_URL = SPOTIFY_ALBUM_TRACKS_URL_TEMPLATE.format(album_id=album_id)
        data = AlbumFetchDAO._request(SPOTIFY_ALBUMS_URL, access_token, params)
        return Tracks.model_validate(data)

    @staticmethod
    def fetch_saved_albums(
        access_token: str,
        limit: int = 20,
        offset: int = 0
    ) -> Albums:
        """Retrieve the user's saved albums.

        Keyword arguments:
        access_token -- a valid Spotify access token
        limit -- number of saved albums to retrieve (default 20)
        offset -- offset for pagination (default 0)
        """
        params: Dict[str, Any] = {"limit": limit, "offset": offset}
        data = AlbumFetchDAO._request(SPOTIFY_SAVED_ALBUMS_URL, access_token, params)
        return Albums.model_validate(data)

    @staticmethod
    def fetch_check_album_is_saved(
        access_token: str,
        album_ids: List[str]
    ) -> List[bool]:
        """Check if specified albums are saved by the user.

        Keyword arguments:
        access_token -- a valid Spotify access token
        album_ids -- list of album IDs to check
        """
        query = ",".join(album_ids)
        data = AlbumFetchDAO._request(f"{SPOTIFY_CHECK_SAVED_ALBUMS_URL}?ids={query}", access_token)
        return data
