from sqlalchemy import ForeignKey, Column, Sequence, String, Integer, Date
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import ARRAY
from models.sql_alchemy_models.base import Base
from models.sql_alchemy_models.association import release_artist

release_id_seq = Sequence(
    "release_id_seq", start=1, increment=1, metadata=Base.metadata
)


class Release(Base):
    __tablename__ = "release"
    id = Column(Integer, release_id_seq, primary_key=True)
    spotify_id = Column(String(22), nullable=False, unique=True)
    release_type = Column(String(22), nullable=False)
    name = Column(String(255), nullable=False)
    popularity = Column(Integer)
    image = Column(String(255), nullable=False)
    release_date = Column(String(20), nullable=False)
    total_tracks = Column(Integer, nullable=False)

    spotify_tracks = relationship("SpotifyTrack", back_populates="release")
    artists = relationship(
        "Artist", back_populates="releases", secondary=release_artist
    )
