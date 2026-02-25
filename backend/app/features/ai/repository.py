from __future__ import annotations

from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.features.ai.models import LLMCacheEntry, AIGenerationEvent


class AIIOpsRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_cache_by_hash(self, prompt_hash: str) -> LLMCacheEntry | None:
        res = await self.db.execute(select(LLMCacheEntry).where(LLMCacheEntry.prompt_hash == prompt_hash))
        return res.scalars().first()

    async def create_cache_entry(
        self,
        *,
        prompt_hash: str,
        prompt: str,
        response_json: dict,
        provider: str | None = None,
        model: str | None = None,
    ) -> LLMCacheEntry:
        obj = LLMCacheEntry(
            prompt_hash=prompt_hash,
            prompt=prompt,
            response_json=response_json,
            provider=provider,
            model=model,
        )
        self.db.add(obj)
        return obj

    async def create_event(
        self,
        *,
        enrollment_id: Any | None,
        generated_lesson_id: Any | None,
        operation: str,
        provider: str | None,
        model: str | None,
        generation_mode: str | None,
        latency_ms: int | None,
        repair_count: int | None,
        quality_status: str | None,
        error_codes: list[str] | None,
    ) -> AIGenerationEvent:
        obj = AIGenerationEvent(
            enrollment_id=enrollment_id,
            generated_lesson_id=generated_lesson_id,
            operation=operation,
            provider=provider,
            model=model,
            generation_mode=generation_mode,
            latency_ms=latency_ms,
            repair_count=repair_count,
            quality_status=quality_status,
            error_codes=error_codes,
        )
        self.db.add(obj)
        return obj
