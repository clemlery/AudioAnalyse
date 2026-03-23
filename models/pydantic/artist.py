# models/artist.py
from pydantic import conint
from models.data_class_models.simplified_artist import SimplifiedArtist
from typing import List
from models.data_class_models.followers import Followers
from models.data_class_models.image import Image


class Artist(SimplifiedArtist):
    followers: Followers
    genres: List[str]
    images: List[Image]
    popularity: conint(ge=0, le=100)  # 0 ≤ popularity ≤ 100
