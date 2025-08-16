from models.sql_alchemy_models.base import Base
from sqlalchemy.orm import relationship
from sqlalchemy import Date, ForeignKey, Column, Integer, String



class TrackStreamDay(Base):
    __tablename__ = 'track_stream_day'
    track_id = Column(Integer, ForeignKey('track.id'), primary_key=True)
    user_id = Column(String, ForeignKey('user.id'), primary_key=True) 
    date = Column(Date, primary_key=True)
    track_done_count = Column(Integer, nullable=False, default=0)
    skipped_count = Column(Integer, nullable=False, default=0)
    click_row_count = Column(Integer, nullable=False, default=0)
    highest_loop_streak = Column(Integer, nullable=False, default=0)
    total_duration_play_s = Column(Integer, nullable=False)

    track = relationship("Track", back_populates='stream_day')
    user = relationship("User", back_populates='stream_day')