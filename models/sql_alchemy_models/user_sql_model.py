from models.sql_alchemy_models.base import Base
from sqlalchemy import Column, Integer, String, DateTime, func
from sqlalchemy.orm import relationship

class User(Base):
    __tablename__ = 'user'
    id = Column(String(28), primary_key=True)
    display_name = Column(String(255), nullable=False)
    email = Column(String(255), nullable=False, unique=True)
    country = Column(String(2), nullable=False)
    product = Column(String(10), nullable=False) # User's subscription level
    access_token = Column(String(1024), nullable=False)
    refresh_token = Column(String(1024), nullable=False)
    expires_in = Column(Integer)
    created_at = Column(DateTime(timezone=True) ,server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True) ,server_default=func.now(), nullable=False)
    token_last_update = Column(DateTime(timezone=True) ,server_default=func.now(), nullable=False)
    
    streams = relationship("TrackStream", back_populates="user")
    stream_day = relationship("TrackStreamDay", back_populates="user")
    