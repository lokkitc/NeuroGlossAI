from datetime import datetime, timedelta, timezone
from typing import Any, Union
import secrets
import hashlib
import hmac
from jose import jwt
from passlib.context import CryptContext
from app.core.config import settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def create_access_token(subject: Union[str, Any], expires_delta: timedelta = None) -> str:
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    
                                                                        
    to_encode = {"exp": expire, "sub": str(subject)}
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)


def create_refresh_token() -> str:
    return secrets.token_urlsafe(48)


def legacy_hash_refresh_token(token: str) -> str:
    return hashlib.sha256((token or "").encode("utf-8", errors="ignore")).hexdigest()


def hash_refresh_token(token: str) -> str:
    key = (settings.SECRET_KEY or "").encode("utf-8", errors="ignore")
    msg = (token or "").encode("utf-8", errors="ignore")
    return hmac.new(key, msg, hashlib.sha256).hexdigest()
