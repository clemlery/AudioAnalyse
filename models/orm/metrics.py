# models/sql_alchemy_models/metrics.py

from sqlalchemy import (
    BigInteger,
    Column,
    DateTime,
    ForeignKey,
    Integer,
    Sequence,
    UniqueConstraint,
    text,
)
from models.orm.base import Base
from sqlalchemy.orm import relationship

track_id_seq = Sequence(
    "track_metrics_snapshot_id_seq", start=0, increment=1, metadata=Base.metadata
)

artist_id_seq = Sequence(
    "artist_metrics_snapshot_id_seq", start=0, increment=1, metadata=Base.metadata
)


class TrackMetricsSnapshot(Base):
    __tablename__ = "track_metrics_snapshot"
    id = Column(Integer, track_id_seq, primary_key=True)
    track_id = Column(Integer, ForeignKey("track.id"), index=True, nullable=False)
    collected_at = Column(DateTime, index=True, nullable=False)
    playcount = Column(BigInteger, nullable=True)

    track = relationship("Track", back_populates="track_metrics")


class ArtistMetricsSnapshot(Base):
    __tablename__ = "artist_metrics_snapshot"
    id = Column(Integer, artist_id_seq, primary_key=True)
    artist_id = Column(Integer, ForeignKey("artist.id"), index=True, nullable=False)
    collected_at = Column(DateTime, index=True, nullable=False)
    monthly_listeners = Column(BigInteger, nullable=True)

    artist = relationship("Artist", back_populates="artist_metrics")
