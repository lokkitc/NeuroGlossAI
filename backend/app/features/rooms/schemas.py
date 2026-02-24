from pydantic import BaseModel
from uuid import UUID


class RoomBase(BaseModel):
    title: str
    description: str = ""
    is_public: bool = False
    is_nsfw: bool = False


class RoomCreate(RoomBase):
    participant_character_ids: list[UUID] = []


class RoomUpdate(BaseModel):
    title: str | None = None
    description: str | None = None
    is_public: bool | None = None
    is_nsfw: bool | None = None


class RoomParticipantOut(BaseModel):
    id: UUID
    room_id: UUID
    character_id: UUID
    priority: int
    is_pinned: bool

    class Config:
        from_attributes = True


class RoomOut(RoomBase):
    id: UUID
    owner_user_id: UUID
    participants: list[RoomParticipantOut] = []

    class Config:
        from_attributes = True
