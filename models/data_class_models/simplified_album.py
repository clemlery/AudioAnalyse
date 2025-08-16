# models/simplified_album.py
from typing import Literal
import re
from pydantic import BaseModel, conlist, constr, conint, HttpUrl, model_validator
from models.data_class_models.external_urls import ExternalUrls
from models.data_class_models.image import Image
from models.data_class_models.simplified_artist import SimplifiedArtist
from models.data_class_models.spotify_id import SpotifyID
from models.data_class_models.available_markets import AvailableMarkets

class SimplifiedAlbum(BaseModel):
    album_type: Literal['album', 'single', 'compilation', 'appears_on']
    artists: conlist(SimplifiedArtist, min_length=1)
    available_markets: AvailableMarkets # type: ignore
    external_urls: ExternalUrls
    href: HttpUrl
    id: SpotifyID # type: ignore
    images: conlist(Image, min_length=1)
    name: constr(min_length=1)
    release_date: constr(pattern=r'^\d{4}(?:-\d{2}(?:-\d{2})?)?$')
    release_date_precision: Literal['year', 'month', 'day']
    total_tracks: conint(ge=1)
    type: Literal['album']
    uri: constr(pattern=r'^spotify:album:[A-Za-z0-9]{22}$')

    @model_validator(mode='after')
    def check_release_date_matches_precision(self):
        date = self.release_date
        precision = self.release_date_precision
        if precision == 'year' and not re.fullmatch(r'\d{4}', date):
            raise ValueError('Pour precision "year", release_date doit être au format YYYY')
        if precision == 'month' and not re.fullmatch(r'\d{4}-\d{2}', date):
            raise ValueError('Pour precision "month", release_date doit être au format YYYY-MM')
        if precision == 'day' and not re.fullmatch(r'\d{4}-\d{2}-\d{2}', date):
            raise ValueError('Pour precision "day", release_date doit être au format YYYY-MM-DD')
        return self
