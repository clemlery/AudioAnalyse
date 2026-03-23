# models/artists.py
from typing import Union, List
from models.pydantic.paginated_response import PaginatedResponse
from models.pydantic.artist import Artist
from models.pydantic.simplified_artist import SimplifiedArtist


class Artists(PaginatedResponse):
    # items peut contenir soit des Artist, soit des SimplifiedArtist
    items: List[Union[Artist, SimplifiedArtist]]
