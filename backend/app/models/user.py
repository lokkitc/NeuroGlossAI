import uuid
from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, JSON
from app.models.custom_types import GUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.models.base import Base

class User(Base):
    __tablename__ = "users"

    id = Column(GUID, primary_key=True, default=uuid.uuid4)
    username = Column(String, unique=True, index=True)
    email = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    
    # Настройки языка (Текущий курс)
    native_language = Column(String, default="Russian")
    target_language = Column(String, default="Kazakh")

    # Геймификация
    xp = Column(Integer, default=0)
    language_levels = Column(JSON, default=dict) # {"Kazakh": "A1", "English": "B2"}
    interests = Column(JSON, default=list) # Список интересов пользователя (например, ["Mobile Legends", "Cooking"])
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    streaks = relationship("Streak", back_populates="user")
