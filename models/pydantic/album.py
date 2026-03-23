# models/album.py
from pydantic import BaseModel, conlist, constr, conint
from typing import List, Optional
from models.pydantic.restrictions import Restrictions
from models.pydantic.external_ids import ExternalIds
from models.pydantic.tracks import Tracks
from models.pydantic.copyright import Copyright
from models.pydantic.simplified_album import SimplifiedAlbum


class Album(SimplifiedAlbum):
    restrictions: Optional[Restrictions] = None
    tracks: Tracks
    copyrights: Optional[List[Copyright]] = None
    external_ids: ExternalIds
    genres: Optional[List[str]] = []
    label: constr(min_length=1)
    popularity: conint(ge=0, le=100)  # 0 ≤ popularity ≤ 100
