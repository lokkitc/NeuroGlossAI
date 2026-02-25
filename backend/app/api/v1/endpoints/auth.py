from typing import Any
from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime, timedelta
import uuid

from app.api import deps
from app.core import security
from app.features.auth.service import AuthService
from app.features.users.schemas import UserCreate, UserResponse, Token, RefreshTokenRequest
from app.features.users.models import User
from app.core.rate_limit import limiter
from app.core.config import settings
from app.features.auth.repository import RefreshTokenRepository
from app.features.auth.models import RefreshToken

router = APIRouter()

@router.post("/register", response_model=UserResponse)
async def register(
    user_in: UserCreate,
    db: AsyncSession = Depends(deps.get_db)
) -> Any:
    user = await AuthService.get_user_by_username(db, user_in.username)
    if user:
        raise HTTPException(
            status_code=400,
            detail="The user with this username already exists in the system.",
        )
    user = await AuthService.create_user(db, user_in)
    return user

@router.post("/login", response_model=Token)
@limiter.limit("10/minute")
async def login(
    request: Request,
    db: AsyncSession = Depends(deps.get_db),
    form_data: OAuth2PasswordRequestForm = Depends()
) -> Any:
    user = await AuthService.authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token = security.create_access_token(subject=user.id)

                                 
    session_id = request.headers.get("X-Session-Id") or request.headers.get("X-Device-Id") or str(uuid.uuid4())
    device_id = request.headers.get("X-Device-Id")

    refresh_token = security.create_refresh_token()
    refresh_hash = security.hash_refresh_token(refresh_token)
    expires_at = datetime.utcnow() + timedelta(days=int(settings.REFRESH_TOKEN_EXPIRE_DAYS or 30))

    repo = RefreshTokenRepository(db)

                                                
    await repo.revoke_active_for_session(user_id=user.id, session_id=session_id)
    await repo.create(
        RefreshToken(
            user_id=user.id,
            session_id=session_id,
            device_id=device_id,
            token_hash=refresh_hash,
            expires_at=expires_at,
            revoked=False,
        ),
        commit=True,
    )

                                             
    await repo.enforce_active_session_limit(user_id=user.id, limit=10, now=datetime.utcnow())
    await db.commit()

    return {"access_token": access_token, "refresh_token": refresh_token, "token_type": "bearer", "session_id": session_id}


@router.post("/refresh", response_model=Token)
@limiter.limit("20/minute")
async def refresh_access_token(
    request: Request,
    body: RefreshTokenRequest,
    db: AsyncSession = Depends(deps.get_db),
) -> Any:
    now = datetime.utcnow()
    repo = RefreshTokenRepository(db)
    token_hash = security.hash_refresh_token(body.refresh_token)
    legacy_hash = security.legacy_hash_refresh_token(body.refresh_token)
    rt = await repo.get_active_by_hash(token_hash=token_hash, now=now)
    if rt is None:
        rt = await repo.get_active_by_hash(token_hash=legacy_hash, now=now)
    if rt is None:
                                                                                                                           
        any_rt = await repo.get_by_hash(token_hash=token_hash)
        if any_rt is None:
            any_rt = await repo.get_by_hash(token_hash=legacy_hash)
        if any_rt is not None:
            await repo.revoke_all_for_user(user_id=any_rt.user_id)
            await db.commit()
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
    await repo.create(new_row, commit=False)

    rt.last_used_at = now
    await repo.revoke(token=rt, replaced_by_id=new_row.id)

    await db.commit()

    access_token = security.create_access_token(subject=rt.user_id)
                                             
    await repo.enforce_active_session_limit(user_id=rt.user_id, limit=10, now=now)
    await db.commit()
    return {"access_token": access_token, "refresh_token": new_refresh, "token_type": "bearer", "session_id": rt.session_id}


@router.post("/logout")
@limiter.limit("20/minute")
async def logout(
    request: Request,
    body: RefreshTokenRequest,
    db: AsyncSession = Depends(deps.get_db),
) -> Any:
    now = datetime.utcnow()
    repo = RefreshTokenRepository(db)
    token_hash = security.hash_refresh_token(body.refresh_token)
    legacy_hash = security.legacy_hash_refresh_token(body.refresh_token)
    rt = await repo.get_active_by_hash(token_hash=token_hash, now=now)
    if rt is None:
        rt = await repo.get_active_by_hash(token_hash=legacy_hash, now=now)
    if rt is None:
        return {"status": "ok"}

    rt.last_used_at = now
    await repo.revoke(token=rt)
    await db.commit()
    return {"status": "ok"}


@router.post("/logout-all")
@limiter.limit("10/minute")
async def logout_all(
    request: Request,
    current_user: User = Depends(deps.get_current_user),
    db: AsyncSession = Depends(deps.get_db),
) -> Any:
    repo = RefreshTokenRepository(db)
    await repo.revoke_all_for_user(user_id=current_user.id)
    await db.commit()
    return {"status": "ok"}


@router.post("/refresh/cleanup")
@limiter.limit("5/minute")
async def cleanup_refresh_tokens(
    request: Request,
    current_user: User = Depends(deps.get_current_user),
    db: AsyncSession = Depends(deps.get_db),
) -> Any:
                                       
    now = datetime.utcnow()
    repo = RefreshTokenRepository(db)
    deleted = await repo.delete_expired(now=now)
    await db.commit()
    return {"status": "ok", "deleted": deleted}

@router.get("/me", response_model=UserResponse)
async def read_users_me(
    current_user: User = Depends(deps.get_current_user),
) -> Any:
    return current_user
