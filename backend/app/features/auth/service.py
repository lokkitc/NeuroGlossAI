from __future__ import annotations

from datetime import datetime, timedelta
import uuid

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core import security
from app.core.config import settings
from app.core.security import get_password_hash, verify_password
from app.features.auth.models import RefreshToken
from app.features.auth.repository import RefreshTokenRepository
from app.features.users.schemas import UserCreate
from app.features.users.repository import UserRepository
from app.features.users.models import User


class AuthService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.users = UserRepository(db)
        self.refresh_tokens = RefreshTokenRepository(db)

    async def get_user_by_username(self, username: str):
        return await self.users.get_by_username(username)

    async def get_user_by_username_or_email(self, identifier: str):
        return await self.users.get_by_username_or_email(identifier)

    async def create_user(self, user_in: UserCreate):
        hashed_password = get_password_hash(user_in.password)
        db_user = User(
            username=user_in.username,
            email=user_in.email,
            hashed_password=hashed_password,
            language_levels={},
        )

        async with self.db.begin():
            await self.users.create(db_user)

        await self.db.refresh(db_user)
        return db_user

    async def authenticate_user(self, username: str, password: str):
        user = await self.get_user_by_username_or_email(username)
        if not user:
            return None
        if not verify_password(password, user.hashed_password):
            return None
        return user

    async def login(self, *, user: User, session_id: str | None, device_id: str | None) -> dict:
        sid = (session_id or "").strip() or (device_id or "").strip() or str(uuid.uuid4())

        access_token = security.create_access_token(subject=user.id)
        refresh_token = security.create_refresh_token()
        refresh_hash = security.hash_refresh_token(refresh_token)
        expires_at = datetime.utcnow() + timedelta(days=int(settings.REFRESH_TOKEN_EXPIRE_DAYS or 30))

        async with self.db.begin():
            await self.refresh_tokens.revoke_active_for_session(user_id=user.id, session_id=sid)
            await self.refresh_tokens.create(
                RefreshToken(
                    user_id=user.id,
                    session_id=sid,
                    device_id=device_id,
                    token_hash=refresh_hash,
                    expires_at=expires_at,
                    revoked=False,
                ),
            )
            await self.refresh_tokens.enforce_active_session_limit(user_id=user.id, limit=10, now=datetime.utcnow())

        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
            "session_id": sid,
        }

    async def refresh(self, *, refresh_token: str) -> dict:
        now = datetime.utcnow()
        token_hash = security.hash_refresh_token(refresh_token)
        legacy_hash = security.legacy_hash_refresh_token(refresh_token)

        rt = await self.refresh_tokens.get_active_by_hash(token_hash=token_hash, now=now)
        if rt is None:
            rt = await self.refresh_tokens.get_active_by_hash(token_hash=legacy_hash, now=now)

        if rt is None:
            any_rt = await self.refresh_tokens.get_by_hash(token_hash=token_hash)
            if any_rt is None:
                any_rt = await self.refresh_tokens.get_by_hash(token_hash=legacy_hash)
            if any_rt is not None:
                async with self.db.begin():
                    await self.refresh_tokens.revoke_all_for_user(user_id=any_rt.user_id)
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token")

        new_refresh = security.create_refresh_token()
        new_hash = security.hash_refresh_token(new_refresh)
        new_expires_at = now + timedelta(days=int(settings.REFRESH_TOKEN_EXPIRE_DAYS or 30))

        new_row = RefreshToken(
            user_id=rt.user_id,
            session_id=rt.session_id,
            device_id=rt.device_id,
            token_hash=new_hash,
            expires_at=new_expires_at,
            revoked=False,
        )

        async with self.db.begin():
            await self.refresh_tokens.create(new_row)
            rt.last_used_at = now
            await self.refresh_tokens.revoke(token=rt, replaced_by_id=new_row.id)

            await self.refresh_tokens.enforce_active_session_limit(user_id=rt.user_id, limit=10, now=now)

        access_token = security.create_access_token(subject=rt.user_id)
        return {
            "access_token": access_token,
            "refresh_token": new_refresh,
            "token_type": "bearer",
            "session_id": rt.session_id,
        }

    async def logout(self, *, refresh_token: str) -> dict:
        now = datetime.utcnow()
        token_hash = security.hash_refresh_token(refresh_token)
        legacy_hash = security.legacy_hash_refresh_token(refresh_token)

        rt = await self.refresh_tokens.get_active_by_hash(token_hash=token_hash, now=now)
        if rt is None:
            rt = await self.refresh_tokens.get_active_by_hash(token_hash=legacy_hash, now=now)
        if rt is None:
            return {"status": "ok"}

        async with self.db.begin():
            rt.last_used_at = now
            await self.refresh_tokens.revoke(token=rt)

        return {"status": "ok"}

    async def logout_all(self, *, user_id) -> dict:
        async with self.db.begin():
            await self.refresh_tokens.revoke_all_for_user(user_id=user_id)
        return {"status": "ok"}

    async def cleanup_refresh_tokens(self) -> dict:
        now = datetime.utcnow()
        async with self.db.begin():
            deleted = await self.refresh_tokens.delete_expired(now=now)
        return {"status": "ok", "deleted": deleted}
