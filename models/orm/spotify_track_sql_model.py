from models.orm.base import Base
from sqlalchemy import Column, ForeignKey, Integer, Sequence, String
from sqlalchemy.orm import relationship

spotify_track_id_seq = Sequence(
    "spotify_track_id_seq", start=0, increment=1, metadata=Base.metadata
)


class SpotifyTrack(Base):
    __tablename__ = "spotify_track"
    track_id = Column(Integer, ForeignKey("track.id"))
    id = Column(Integer, spotify_track_id_seq, primary_key=True)
    spotify_id = Column(String(22), nullable=False, unique=True)
    release_id = Column(Integer, ForeignKey("release.id"))

    canonical = relationship("Track", back_populates="appearances")
    release = relationship("Release", back_populates="spotify_tracks")
