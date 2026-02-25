import uuid

from sqlalchemy import Column, DateTime, String, Boolean, Integer, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.models.base import Base
from app.models.custom_types import GUID


class Room(Base):
    __tablename__ = "rooms"

    id = Column(GUID, primary_key=True, default=uuid.uuid4)

    owner_user_id = Column(GUID, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)

    title = Column(String, nullable=False, default="")
    description = Column(String, nullable=False, default="")

    is_public = Column(Boolean, nullable=False, default=False)
    is_nsfw = Column(Boolean, nullable=False, default=False)

    created_at = Column(DateTime(timezone=True), server_default=func.now())

    owner = relationship("User", back_populates=None)
    participants = relationship(
        "RoomParticipant",
        back_populates="room",
        cascade="all, delete-orphan",
    )


class RoomParticipant(Base):
    __tablename__ = "room_participants"
    __table_args__ = (
        UniqueConstraint("room_id", "character_id", name="uq_room_character"),
    )

    id = Column(GUID, primary_key=True, default=uuid.uuid4)

    room_id = Column(GUID, ForeignKey("rooms.id", ondelete="CASCADE"), nullable=False)
    character_id = Column(GUID, ForeignKey("characters.id", ondelete="CASCADE"), nullable=False)

                                                  
    priority = Column(Integer, nullable=False, default=0)
                                                                              
    is_pinned = Column(Boolean, nullable=False, default=False)

    created_at = Column(DateTime(timezone=True), server_default=func.now())

    room = relationship("Room", back_populates="participants")
    character = relationship("Character")
