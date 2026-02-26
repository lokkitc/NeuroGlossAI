from __future__ import annotations

from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID

from app.core.exceptions import EntityNotFoundException, NeuroGlossException
from app.features.themes.models import Theme
from app.features.themes.repository import ThemeRepository
from app.features.themes.schemas import ThemeCreate
from app.features.characters.repository import CharacterRepository


class ThemeService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.themes = ThemeRepository(db)
        self.characters = CharacterRepository(db)

    async def list_available(self, *, user_id: UUID, theme_type: str | None, skip: int, limit: int):
        return await self.themes.list_available(user_id=user_id, theme_type=theme_type, skip=skip, limit=limit)

    async def create_my_theme(self, *, user_id: UUID, body: ThemeCreate) -> Theme:
        existing = await self.themes.get_by_owner_and_slug(owner_user_id=user_id, slug=body.slug)
        if existing is not None:
            raise NeuroGlossException(status_code=409, code="conflict", detail="Theme slug already exists")

        row = Theme(
            theme_type=body.theme_type.value,
            slug=body.slug,
            display_name=body.display_name,
            description=body.description or "",
            is_public=bool(body.is_public),
            owner_user_id=user_id,
            light_tokens=body.light_tokens.model_dump(by_alias=True) if body.light_tokens is not None else None,
            dark_tokens=body.dark_tokens.model_dump(by_alias=True) if body.dark_tokens is not None else None,
        )

        async with self.db.begin():
            await self.themes.create(row)

        await self.db.refresh(row)

        return row

    async def select_my_ui_theme_for_user(self, *, current_user, theme_id: UUID) -> dict[str, Any]:
        theme = await self.themes.get_available(theme_id=theme_id, user_id=current_user.id)
        if theme is None:
            raise EntityNotFoundException("Theme", theme_id)

        async with self.db.begin():
            current_user.selected_theme_id = theme.id
            self.db.add(current_user)

        await self.db.refresh(current_user)

        return {"status": "ok", "selected_theme_id": str(current_user.selected_theme_id)}

    async def select_character_chat_theme(self, *, owner_user_id: UUID, character_id: UUID, theme_id: UUID) -> dict[str, Any]:
        ch = await self.characters.get(character_id)
        if not ch or ch.owner_user_id != owner_user_id:
            raise EntityNotFoundException("Character", character_id)

        theme = await self.themes.get_available(theme_id=theme_id, user_id=owner_user_id)
        if theme is None:
            raise EntityNotFoundException("Theme", theme_id)

        async with self.db.begin():
            ch.chat_theme_id = theme.id
            self.db.add(ch)

        await self.db.refresh(ch)

        return {"status": "ok", "character_id": str(ch.id), "chat_theme_id": str(ch.chat_theme_id)}
