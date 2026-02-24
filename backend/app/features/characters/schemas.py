from pydantic import BaseModel, field_validator
from uuid import UUID


class CharacterBase(BaseModel):
    slug: str
    display_name: str
    description: str = ""
    system_prompt: str
    style_prompt: str | None = None
    is_public: bool = False
    is_nsfw: bool = False
    settings: dict | None = None

    @field_validator("slug")
    @classmethod
    def _slug(cls, v: str):
        v = (v or "").strip()
        if not v:
            raise ValueError("slug is required")
        if len(v) > 64:
            raise ValueError("slug too long")
        return v


class CharacterCreate(CharacterBase):
    pass


class CharacterUpdate(BaseModel):
    display_name: str | None = None
    description: str | None = None
    system_prompt: str | None = None
    style_prompt: str | None = None
    is_public: bool | None = None
    is_nsfw: bool | None = None
    settings: dict | None = None


class CharacterOut(CharacterBase):
    id: UUID
    owner_user_id: UUID

    class Config:
        from_attributes = True
