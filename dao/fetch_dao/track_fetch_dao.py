"""dao/fetch_dao/track_fetch_dao.py

Contains the Fetch DAO (Data Access Object) for all operations related to Spotify tracks.
Each method corresponds to a Spotify API REST endpoint returning tracks or associated information.
"""

from dao.base_dao import BaseFetchDAO

from pydantic import ValidationError

from models.data_class_models.recently_played_tracks import RecentlyPlayedTracks
from models.data_class_models.track import Track
from models.data_class_models.playlist_track import PlaylistTrack
from models.data_class_models.tracks import Tracks
from typing import Any, Dict, List, Optional, Set

from constants.api import (
    SPOTIFY_TRACKS_URL,
    SPOTIFY_SAVED_TRACKS_URL,
    SPOTIFY_TRACK_IS_SAVED_URL,
    SPOTIFY_RECENT_PLAY_HISTORY_URL,
    SPOTIFY_TOP_TRACKS_URL,
    SPOTIFY_PLAYLIST_TRACKS_URL_TEMPLATE,
)

class TrackFetchDAO(BaseFetchDAO):
    """
    Data Access Object for Spotify tracks.
    Groups methods to retrieve tracks, saved tracks, playback history,
    top tracks, and playlist items via the Spotify API.
    """
    @staticmethod
    def fetch_track(
        access_token: str,
        track_id: str
    ) -> Track:
        """Retrieve a single track by its ID.

        Keyword arguments:
        access_token -- a valid Spotify access token
        track_id -- the ID of the track to retrieve
        """
        data = TrackFetchDAO._request(f"{SPOTIFY_TRACKS_URL}/{track_id}", access_token)
        return Track.model_validate(data)

    @staticmethod
    def fetch_tracks(
        access_token: str,
        track_ids: List[str] | Set[str]
    ) -> List[Track]:
        """Retrieve multiple tracks by their IDs.

        Keyword arguments:
        access_token -- a valid Spotify access token
        track_ids -- a list or set of track IDs to retrieve
        """
        query = ",".join(track_ids)
        data = TrackFetchDAO._request(f"{SPOTIFY_TRACKS_URL}?ids={query}", access_token)
        tracks = []
        for item in data.get('tracks', []):
            try:
                track = Track.model_validate(item)
                tracks.append(track)
            except ValidationError:
                continue
        return tracks

    @staticmethod
    def fetch_saved_tracks(
        access_token: str,
        market: Optional[str] = None,
        limit: int = 20,
        offset: int = 0
    ) -> Tracks:
        """Retrieve the user's saved tracks.

        Keyword arguments:
        access_token -- a valid Spotify access token
        market -- market code for availability filtering
        limit -- number of saved tracks to retrieve (default 20)
        offset -- offset for pagination (default 0)
        """
        params: Dict[str, Any] = {"limit": limit, "offset": offset}
        if market:
            params["market"] = market
        data = TrackFetchDAO._request(SPOTIFY_SAVED_TRACKS_URL, access_token, params)
        return Tracks.model_validate(data)

    @staticmethod
    def fetch_check_track_is_saved(
        access_token: str,
        track_ids: List[str]
    ) -> List[bool]:
        """Check if specified tracks are saved by the user.

        Keyword arguments:
        access_token -- a valid Spotify access token
        track_ids -- list of track IDs to check
        """
        query = ",".join(track_ids)
        data = TrackFetchDAO._request(f"{SPOTIFY_TRACK_IS_SAVED_URL}?ids={query}", access_token)
        return data

    @staticmethod
    def fetch_play_history(
        access_token: str,
        limit: int = 20,
        after: Optional[str] = None,
        before: Optional[str] = None
    ) -> RecentlyPlayedTracks:
        """Retrieve the user's playback history.

        Keyword arguments:
        access_token -- a valid Spotify access token
        limit -- number of tracks from history to retrieve (default 20)
        after -- timestamp after which to retrieve tracks
        before -- timestamp before which to retrieve tracks
        """
        params: Dict[str, Any] = {"limit": limit}
        if after:
            params["after"] = after
        elif before:
            params["before"] = before
        data = TrackFetchDAO._request(SPOTIFY_RECENT_PLAY_HISTORY_URL, access_token, params)
        return RecentlyPlayedTracks.model_validate(data)

    def fetch_top_tracks(
        access_token: str,
        time_range: str = "medium_term",
        limit: int = 20
    ) -> Tracks:
        """Retrieve the user's top tracks for a specified time range.

        Keyword arguments:
        access_token -- a valid Spotify access token
        time_range -- time range for the top tracks (default 'medium_term')
        limit -- number of top tracks to retrieve (default 20)
        """
        params: Dict[str, Any] = {"time_range": time_range, "limit": limit}
        data = TrackFetchDAO._request(SPOTIFY_TOP_TRACKS_URL, access_token, params)
        return Tracks.model_validate(data)

    def fetch_playlist_item(
        access_token: str,
        playlist_id: str,
        market: Optional[str] = None,
        fields: Optional[str] = None,
        limit: int = 20,
        offset: int = 0,
        additional_types: str = 'track'
    ) -> List[PlaylistTrack]:
        """Retrieve items from a given playlist.

        Keyword arguments:
        access_token -- a valid Spotify access token
        playlist_id -- the ID of the playlist
        market -- market code for availability filtering
        fields -- specific fields to retrieve
        limit -- number of playlist items to retrieve (default 20)
        offset -- offset for pagination (default 0)
        additional_types -- types of additional items to include (default 'track')
        """
        params: Dict[str, Any] = {"limit": limit, "offset": offset, "additional_types": additional_types}
        if market:
            params["market"] = market
        if fields:
            params["fields"] = fields
        url = SPOTIFY_PLAYLIST_TRACKS_URL_TEMPLATE.format(playlist_id=playlist_id)
        data = TrackFetchDAO._request(url, access_token, params)
        return Tracks.model_validate(data)