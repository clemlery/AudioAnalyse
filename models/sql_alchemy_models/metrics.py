# models/sql_alchemy_models/metrics.py
from sqlalchemy import BigInteger, Column, DateTime, ForeignKey, Integer, Sequence, String, UniqueConstraint, text
from models.sql_alchemy_models.base import Base

track_id_seq = Sequence(
    'track_metrics_id_seq',
    start=0,
    increment=1,
    metadata=Base.metadata
)

artist_id_seq = Sequence(
    'artist_metrics_id_seq',
    start=0,
    increment=1,
    metadata=Base.metadata
)

class TrackMetricsSnapshot(Base):
    __tablename__ = "track_metrics_snapshot"
    id = Column(Integer, track_id_seq, primary_key=True)
    track_id = Column(ForeignKey("track.id"), index=True, nullable=False)
    collected_at = Column(DateTime, index=True, nullable=False)
    playcount = Column(BigInteger, nullable=False)

    __table_args__ = (
        UniqueConstraint("track_id", text("date(collected_at)")),
    )

class ArtistMetricsSnapshot(Base):
    __tablename__ = "artist_metrics_snapshot"
    id = Column(Integer,artist_id_seq, primary_key=True)
    artist_id = Column(ForeignKey("artist.id"), index=True, nullable=False)
    collected_at = Column(DateTime, index=True, nullable=False)
    monthly_listeners = Column(BigInteger, nullable=False)

    __table_args__ = (
        UniqueConstraint("artist_id", text("date(collected_at)")),
    )