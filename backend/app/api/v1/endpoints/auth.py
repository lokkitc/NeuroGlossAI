from typing import Any
from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession

from app.api import deps
from app.features.auth.service import AuthService
from app.features.users.schemas import UserCreate, UserResponse, Token, RefreshTokenRequest
from app.features.users.models import User
from app.core.rate_limit import limiter

router = APIRouter()

@router.post("/register", response_model=UserResponse)
async def register(
    user_in: UserCreate,
    db: AsyncSession = Depends(deps.get_db)
) -> Any:
    svc = AuthService(db)
    user = await svc.get_user_by_username(user_in.username)
    if user:
        raise HTTPException(
            status_code=400,
            detail="The user with this username already exists in the system.",
        )
    user = await svc.create_user(user_in)
    return user

@router.post("/login", response_model=Token)
@limiter.limit("10/minute")
async def login(
    request: Request,
    db: AsyncSession = Depends(deps.get_db),
    form_data: OAuth2PasswordRequestForm = Depends()
) -> Any:
    svc = AuthService(db)
    user = await svc.authenticate_user(form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return await svc.login(
        user=user,
        session_id=request.headers.get("X-Session-Id"),
        device_id=request.headers.get("X-Device-Id"),
    )


@router.post("/refresh", response_model=Token)
@limiter.limit("20/minute")
async def refresh_access_token(
    request: Request,
    body: RefreshTokenRequest,
    db: AsyncSession = Depends(deps.get_db),
) -> Any:
    return await AuthService(db).refresh(refresh_token=body.refresh_token)


@router.post("/logout")
@limiter.limit("20/minute")
async def logout(
    request: Request,
    body: RefreshTokenRequest,
    db: AsyncSession = Depends(deps.get_db),
) -> Any:
    return await AuthService(db).logout(refresh_token=body.refresh_token)


@router.post("/logout-all")
@limiter.limit("10/minute")
async def logout_all(
    request: Request,
    current_user: User = Depends(deps.get_current_user),
    db: AsyncSession = Depends(deps.get_db),
) -> Any:
    return await AuthService(db).logout_all(user_id=current_user.id)


@router.post("/refresh/cleanup")
@limiter.limit("5/minute")
async def cleanup_refresh_tokens(
    request: Request,
    current_user: User = Depends(deps.get_current_user),
    db: AsyncSession = Depends(deps.get_db),
) -> Any:
    return await AuthService(db).cleanup_refresh_tokens()

@router.get("/me", response_model=UserResponse)
async def read_users_me(
    current_user: User = Depends(deps.get_current_user),
) -> Any:
    resp = UserResponse.model_validate(current_user)
    resp.avatar_url = UserResponse._normalize_storageapi_urls(resp.avatar_url)
    resp.thumbnail_url = UserResponse._normalize_storageapi_urls(resp.thumbnail_url)
    resp.banner_url = UserResponse._normalize_storageapi_urls(resp.banner_url)
    return resp
