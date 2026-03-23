# models/recently_played_tracks.py
from models.pydantic.paginated_response import PaginatedResponse
from models.pydantic.play_history import PlayHistory
from typing import List


class RecentlyPlayedTracks(PaginatedResponse):
    items: List[PlayHistory]
