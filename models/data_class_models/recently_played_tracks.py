# models/recently_played_tracks.py
from models.data_class_models.paginated_response import PaginatedResponse
from models.data_class_models.play_history import PlayHistory
from typing import List

class RecentlyPlayedTracks(PaginatedResponse):
    items : List[PlayHistory]