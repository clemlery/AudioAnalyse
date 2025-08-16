# models/album.py
from pydantic import BaseModel, conlist, constr, conint
from typing import List, Optional
from models.data_class_models.restrictions import Restrictions
from models.data_class_models.external_ids import ExternalIds
from models.data_class_models.tracks import Tracks
from models.data_class_models.copyright import Copyright
from models.data_class_models.simplified_album import SimplifiedAlbum


class Album(SimplifiedAlbum):
    restrictions : Optional[Restrictions] = None
    tracks : Tracks
    copyrights : Optional[List[Copyright]] = None
    external_ids : ExternalIds
    genres : Optional[List[str]] = []
    label : constr(min_length=1)
    popularity: conint(ge=0, le=100)    # 0 ≤ popularity ≤ 100
