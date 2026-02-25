from __future__ import annotations

from datetime import datetime
from typing import Optional
from uuid import UUID

from sqlalchemy import select, update, delete, func

from app.features.auth.models import RefreshToken
from app.features.common.db import BaseRepository


class RefreshTokenRepository(BaseRepository[RefreshToken]):
    def __init__(self, db):
        super().__init__(RefreshToken, db)

    async def get_active_by_hash(self, *, token_hash: str, now: datetime) -> Optional[RefreshToken]:
        res = await self.db.execute(
            select(RefreshToken)
            .where(RefreshToken.token_hash == token_hash)
            .where(RefreshToken.revoked.is_(False))
            .where(RefreshToken.expires_at > now)
        )
        return res.scalars().first()

    async def get_by_hash(self, *, token_hash: str) -> Optional[RefreshToken]:
        res = await self.db.execute(select(RefreshToken).where(RefreshToken.token_hash == token_hash))
        return res.scalars().first()

    async def revoke(self, *, token: RefreshToken, replaced_by_id: UUID | None = None) -> RefreshToken:
        token.revoked = True
        if replaced_by_id is not None:
            token.replaced_by_id = replaced_by_id
        self.db.add(token)
        await self.db.flush()
        return token

    async def revoke_all_for_user(self, *, user_id: UUID) -> None:
        await self.db.execute(
            update(RefreshToken)
            .where(RefreshToken.user_id == user_id)
            .where(RefreshToken.revoked.is_(False))
            .values(revoked=True)
        )
        await self.db.flush()

    async def revoke_active_for_session(self, *, user_id: UUID, session_id: str) -> None:
        await self.db.execute(
            update(RefreshToken)
            .where(RefreshToken.user_id == user_id)
            .where(RefreshToken.session_id == session_id)
            .where(RefreshToken.revoked.is_(False))
            .values(revoked=True)
        )
        await self.db.flush()

    async def enforce_active_session_limit(self, *, user_id: UUID, limit: int, now: datetime) -> int:
        """Delete oldest active sessions beyond the limit. Returns number deleted."""
        if limit <= 0:
            return 0

        res = await self.db.execute(
            select(RefreshToken.session_id, func.max(RefreshToken.created_at).label("last_created"))
            .where(RefreshToken.user_id == user_id)
            .where(RefreshToken.revoked.is_(False))
            .where(RefreshToken.expires_at > now)
            .group_by(RefreshToken.session_id)
            .order_by(func.max(RefreshToken.created_at).desc())
        )
        sessions = [r[0] for r in res.all()]
        if len(sessions) <= limit:
            return 0

        to_drop = sessions[limit:]
        del_res = await self.db.execute(
            delete(RefreshToken)
            .where(RefreshToken.user_id == user_id)
            .where(RefreshToken.session_id.in_(to_drop))
        )
        await self.db.flush()
        return int(getattr(del_res, "rowcount", 0) or 0)

    async def delete_expired(self, *, now: datetime) -> int:
        res = await self.db.execute(delete(RefreshToken).where(RefreshToken.expires_at <= now))
        await self.db.flush()
        return int(getattr(res, "rowcount", 0) or 0)
