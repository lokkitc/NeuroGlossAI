import uuid

from sqlalchemy import Column, Integer, String, Boolean, DateTime, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.models.base import Base
from app.models.custom_types import GUID


class User(Base):
    __tablename__ = "users"

    id = Column(GUID, primary_key=True, default=uuid.uuid4)
    username = Column(String, unique=True, index=True)
    email = Column(String, unique=True, index=True)
    hashed_password = Column(String)

    is_admin = Column(Boolean, nullable=False, default=False)

                                    
    native_language = Column(String, default="Russian")
    target_language = Column(String, default="Kazakh")

                  
    xp = Column(Integer, default=0)
    language_levels = Column(JSON, default=dict)                                     
    interests = Column(JSON, default=list)                                 

                              
    avatar_url = Column(String, nullable=True)
    thumbnail_url = Column(String, nullable=True)
    banner_url = Column(String, nullable=True)
    preferred_name = Column(String, nullable=True)
    bio = Column(String, nullable=True)
    timezone = Column(String, nullable=True, default="UTC")
    ui_theme = Column(String, nullable=True, default="system")

                          
    assistant_tone = Column(String, nullable=True, default="friendly")
    assistant_verbosity = Column(Integer, nullable=True, default=3)
    preferences = Column(JSON, default=dict)

    created_at = Column(DateTime(timezone=True), server_default=func.now())

    streaks = relationship("Streak", back_populates="user")
