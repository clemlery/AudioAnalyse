from sqlalchemy import Sequence, Column, String, Integer
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import ARRAY
from models.sql_alchemy_models.base import Base
from models.sql_alchemy_models.association import release_artist, track_artist

artist_id_seq = Sequence(
    'artist_id_seq',
    start=1,
    increment=1,
    metadata=Base.metadata
)

class Artist(Base):
    __tablename__ = 'artist'
    id = Column(Integer, artist_id_seq, primary_key=True)
    spotify_id = Column(String(22), nullable=False, unique=True)
    name = Column(String(255), nullable=False)
    followers = Column(Integer, nullable=False)
    popularity = Column(Integer)
    genres = Column(ARRAY(String(64)), nullable=False)
    image = Column(String(255), nullable=False) 
    
    releases = relationship('Release', back_populates='artists', secondary=release_artist)
    tracks = relationship('Track', secondary=track_artist, back_populates='artists')

