from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID

from app.core.exceptions import EntityNotFoundException
from app.features.common.db import begin_if_needed
from app.features.characters.models import Character
from app.features.characters.repository import CharacterRepository
from app.features.characters.schemas import CharacterCreate, CharacterUpdate


class CharacterService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.characters = CharacterRepository(db)

    async def list_for_owner(self, *, owner_user_id: UUID, skip: int, limit: int):
        return await self.characters.list_for_owner(owner_user_id, skip=skip, limit=limit)

    async def list_public(self, *, skip: int, limit: int, nsfw: bool | None):
        return await self.characters.list_public(skip=skip, limit=limit, nsfw=nsfw)

    async def create_character(self, *, owner_user_id: UUID, body: CharacterCreate) -> Character:
        row = Character(
            owner_user_id=owner_user_id,
            slug=body.slug,
            display_name=body.display_name,
            description=body.description or "",
            system_prompt=body.system_prompt,
            style_prompt=body.style_prompt,
            avatar_url=body.avatar_url,
            thumbnail_url=body.thumbnail_url,
            banner_url=body.banner_url,
            greeting=body.greeting,
            tags=body.tags,
            voice_provider=body.voice_provider,
            voice_id=body.voice_id,
            voice_settings=body.voice_settings,
            chat_settings=body.chat_settings,
            chat_theme_id=body.chat_theme_id,
            is_public=bool(body.is_public),
            is_nsfw=bool(body.is_nsfw),
            settings=body.settings,
        )

        async with begin_if_needed(self.db):
            await self.characters.create(row)

        await self.db.refresh(row)
        return row

    async def update_character(self, *, character_id: UUID, owner_user_id: UUID, body: CharacterUpdate) -> Character:
        ch = await self.characters.get(character_id)
        if not ch or ch.owner_user_id != owner_user_id:
            raise EntityNotFoundException("Character", character_id)

        async with begin_if_needed(self.db):
            await self.characters.update(ch, body)

        await self.db.refresh(ch)
        return ch

    async def delete_character(self, *, character_id: UUID, owner_user_id: UUID) -> dict:
        ch = await self.characters.get(character_id)
        if not ch or ch.owner_user_id != owner_user_id:
            raise EntityNotFoundException("Character", character_id)

        async with begin_if_needed(self.db):
            await self.characters.delete(character_id)

        return {"status": "ok"}
