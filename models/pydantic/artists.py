# models/artists.py
from typing import Union, List
from models.data_class_models.paginated_response import PaginatedResponse
from models.data_class_models.artist import Artist
from models.data_class_models.simplified_artist import SimplifiedArtist


class Artists(PaginatedResponse):
    # items peut contenir soit des Artist, soit des SimplifiedArtist
    items: List[Union[Artist, SimplifiedArtist]]
