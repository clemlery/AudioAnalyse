# models/tracks.py
from typing import Union, List
from pydantic import model_validator, ConfigDict
from models.pydantic.simplified_track import SimplifiedTrack
from models.pydantic.paginated_response import PaginatedResponse
from models.pydantic.playlist_track import PlaylistTrack
from models.pydantic.saved_track import SavedTrack


class Tracks(PaginatedResponse):
    # items peut contenir soit des PlaylistTrack, soit des SimplifiedTrack
    items: List[Union[PlaylistTrack, SimplifiedTrack, SavedTrack]]
    # override de limit pour lever dynamiquement une erreur selon le type d'items
    limit: int

    # configuration Pydantic v2
    model_config = ConfigDict()

    @model_validator(mode="after")
    def check_limit_based_on_item_type(cls, result):
        """
        Après création du modèle :
        - si le premier item est un PlaylistTrack, limit ≤ 100
        - sinon (SimplifiedTrack), limit ≤ 50
        """
        if result.items:
            first_item = result.items[0]
            if isinstance(first_item, PlaylistTrack):
                max_limit = 100
                context = "PlaylistTrack"
            elif isinstance(first_item, SimplifiedTrack):
                max_limit = 50
                context = "SimplifiedTrack"
            else:
                max_limit = 50
                context = "SavedTrack"
            if result.limit > max_limit:
                raise ValueError(
                    f"Pour {context}, limit doit être ≤ {max_limit}, got {result.limit}"
                )
        return result
