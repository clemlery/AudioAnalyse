# models/simplified_track.py
from typing import Optional, Literal
from pydantic import BaseModel, conlist, constr, conint, PositiveInt, HttpUrl
from models.data_class_models.simplified_artist import SimplifiedArtist
from models.data_class_models.external_urls import ExternalUrls
from models.data_class_models.linked_from import LinkedFromTrack
from models.data_class_models.restrictions import Restrictions
from models.data_class_models.spotify_id import SpotifyID
from models.data_class_models.available_markets import AvailableMarkets


class SimplifiedTrack(BaseModel):
    artists: conlist(SimplifiedArtist, min_length=1)  # au moins un artiste
    available_markets: AvailableMarkets  # type: ignore
    disc_number: conint(ge=1)  # >= 1
    duration_ms: PositiveInt  # > 0
    explicit: bool
    external_urls: ExternalUrls
    href: HttpUrl  # URL valide
    id: SpotifyID  # type: ignore
    is_playable: Optional[bool] = None
    linked_from: Optional[LinkedFromTrack] = None
    restrictions: Optional[Restrictions] = None
    name: constr(min_length=1)  # nom non vide
    track_number: conint(ge=1)  # >= 1
    type: Literal["track"]  # toujours "track"
    uri: constr(pattern=r"^spotify:track:[A-Za-z0-9]{22}$")
    is_local: bool
    preview_url: Optional[HttpUrl] = None
