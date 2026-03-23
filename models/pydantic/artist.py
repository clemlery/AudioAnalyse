# models/artist.py
from pydantic import conint
from models.pydantic.simplified_artist import SimplifiedArtist
from typing import List
from models.pydantic.followers import Followers
from models.pydantic.image import Image


class Artist(SimplifiedArtist):
    followers: Followers
    genres: List[str]
    images: List[Image]
    popularity: conint(ge=0, le=100)  # 0 ≤ popularity ≤ 100
