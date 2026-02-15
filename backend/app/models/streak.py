import uuid
from sqlalchemy import Column, Integer, Date, ForeignKey
from app.models.custom_types import GUID
from sqlalchemy.orm import relationship
from app.models.base import Base

class Streak(Base):
    __tablename__ = "streaks"

    id = Column(GUID, primary_key=True, default=uuid.uuid4)
    user_id = Column(GUID, ForeignKey("users.id"))
    
    current_streak = Column(Integer, default=0)
    last_activity_date = Column(Date)
    
    user = relationship("User", back_populates="streaks")
