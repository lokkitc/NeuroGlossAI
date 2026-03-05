from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import jwt, JWTError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.core import security
from app.core.config import settings
from app.core.exceptions import NeuroGlossException
from app.core.database import get_db
from app.features.subscriptions.service import SubscriptionService
from app.features.users.models import User
from app.features.users.schemas import TokenData
from uuid import UUID


def subscription_features_for_tier(tier: str) -> dict[str, bool]:
    t = (tier or "").strip().lower() or "free"
    if t == "pro":
        return {
            "ai_unlimited": True,
            "srs_priority": True,
            "exports": True,
            "themes_premium": True,
        }
    if t == "plus":
        return {
            "ai_unlimited": False,
            "srs_priority": True,
            "exports": True,
            "themes_premium": True,
        }
    return {
        "ai_unlimited": False,
        "srs_priority": False,
        "exports": False,
        "themes_premium": False,
    }


def require_subscription_feature(feature: str):
    async def _dep(
        current_user: User = Depends(get_current_user),
        db: AsyncSession = Depends(get_db),
    ) -> User:
        tier, _, _ = await SubscriptionService(db).get_subscription_status(user_id=current_user.id)
        features = subscription_features_for_tier(tier)
        if not bool(features.get(feature)):
            raise NeuroGlossException(
                status_code=status.HTTP_402_PAYMENT_REQUIRED,
                code="subscription_required",
                detail="Subscription feature required",
                details={"feature": feature, "tier": tier},
            )
        return current_user

    return _dep

oauth2_scheme = OAuth2PasswordBearer(tokenUrl=f"{settings.API_V1_STR}/auth/login")

async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db)
) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        decode_kwargs = {}
        if getattr(settings, "JWT_AUDIENCE", None):
            decode_kwargs["audience"] = settings.JWT_AUDIENCE
        if getattr(settings, "JWT_ISSUER", None):
            decode_kwargs["issuer"] = settings.JWT_ISSUER

        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM],
            **decode_kwargs,
        )
        sub: str = payload.get("sub")
        if sub is None:
            raise credentials_exception
        try:
            user_id = UUID(str(sub))
        except Exception:
            raise credentials_exception
        token_data = TokenData(user_id=user_id)
    except JWTError:
        raise credentials_exception
    
    result = await db.execute(select(User).where(User.id == token_data.user_id))
    user = result.scalars().first()
    
    if user is None:
        raise credentials_exception

    if not getattr(user, "is_active", True):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Inactive user")
    return user


async def require_admin(
    current_user: User = Depends(get_current_user),
) -> User:
    if not getattr(current_user, "is_admin", False):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin access required")
    return current_user
