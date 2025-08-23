from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy import ForeignKey, Column, Sequence, String, Integer
from sqlalchemy.orm import relationship
from models.sql_alchemy_models.base import Base
from models.sql_alchemy_models.association import track_artist

track_id_seq = Sequence("track_id_seq", start=0, increment=1, metadata=Base.metadata)


class Track(Base):
    __tablename__ = "track"
    id = Column(Integer, track_id_seq, primary_key=True)
    name = Column(String(255), nullable=False)
    duration_ms = Column(Integer, nullable=False)

    streams = relationship("TrackStream", back_populates="track")
    artists = relationship("Artist", secondary=track_artist, back_populates="tracks")
    appearances = relationship("SpotifyTrack", back_populates="canonical")
    stream_day = relationship("TrackStreamDay", back_populates="track")
    track_metrics = relationship("TrackMetricsSnapshot", back_populates="track")
