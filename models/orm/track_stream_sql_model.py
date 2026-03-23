from sqlalchemy.orm import relationship
from sqlalchemy import ForeignKey, Column, Index, String, Integer, DateTime
from models.orm.base import Base


class TrackStream(Base):
    __tablename__ = "track_stream"
    user_id = Column(String(28), ForeignKey("user.id"), primary_key=True)
    track_id = Column(Integer, ForeignKey("track.id"), primary_key=True)
    first_played_at = Column(DateTime, nullable=False)
    last_played_at = Column(DateTime, nullable=False)
    track_done_count = Column(Integer, nullable=False, default=0)
    skipped_count = Column(Integer, nullable=False, default=0)
    click_row_count = Column(Integer, nullable=False, default=0)
    highest_loop_streak = Column(Integer, nullable=False, default=0)
    total_duration_play_s = Column(Integer, nullable=False)

    user = relationship("User", back_populates="streams")
    track = relationship("Track", back_populates="streams")

    __table_args__ = (Index("ix_user_played_at", "user_id", "last_played_at"),)
