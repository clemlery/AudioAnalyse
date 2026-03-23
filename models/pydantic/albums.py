# models/albums.py
from typing import Union, List
from models.pydantic.paginated_response import PaginatedResponse
from models.pydantic.album import Album
from models.pydantic.simplified_album import SimplifiedAlbum
from models.pydantic.saved_album import SavedAlbum


class Albums(PaginatedResponse):
    # items peut contenir soit des Album, soit des SimplifiedAlbum, soit des SavedAlbum
    items: List[Union[Album, SimplifiedAlbum, SavedAlbum]]
