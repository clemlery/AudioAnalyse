from models.orm.base import Base
from sqlalchemy import ForeignKey, Column, Integer, Table


release_artist = Table(
    "release_artist",
    Base.metadata,
    Column("release_id", Integer, ForeignKey("release.id"), primary_key=True),
    Column("artist_id", Integer, ForeignKey("artist.id"), primary_key=True),
)

track_artist = Table(
    "track_artist",
    Base.metadata,
    Column("track_id", Integer, ForeignKey("track.id"), primary_key=True),
    Column("artist_id", Integer, ForeignKey("artist.id"), primary_key=True),
)
