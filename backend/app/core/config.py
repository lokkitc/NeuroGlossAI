import json
from typing import List

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    PROJECT_NAME: str = "NeuroGlossAI"
    API_V1_STR: str = "/api/v1"

    # Окружение
    ENV: str = "development"  # development | staging | production
    DEBUG: bool = False
    LOG_LEVEL: str = "INFO"
    
    # База данных
    DATABASE_URL: str
    
    # Безопасность
    SECRET_KEY: str
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 30 # 30 дней
    ALGORITHM: str = "HS256"

    # Sensitive endpoints
    ENABLE_USER_EXPORT: bool = False
    
    # ИИ
    AI_ENABLED: bool = True
    GROQ_API_KEY: str | None = None
    GROQ_FALLBACK_MODELS: List[str] = ["llama-3.1-8b-instant", "llama-3.3-70b-versatile"]
    AI_CIRCUIT_BREAKER_FAIL_THRESHOLD: int = 3
    AI_CIRCUIT_BREAKER_OPEN_SECONDS: int = 60
    
    # Устаревшее
    GEMINI_API_KEY: str = ""

    # CORS
    BACKEND_CORS_ORIGINS: List[str] = ["http://localhost:5173", "http://localhost:3000"]

    @field_validator("BACKEND_CORS_ORIGINS", mode="before")
    @classmethod
    def _parse_cors_origins(cls, v):
        if v is None:
            return []
        if isinstance(v, list):
            return v
        if isinstance(v, str):
            s = v.strip()
            if not s:
                return []
            if s.startswith("["):
                try:
                    parsed = json.loads(s)
                    if isinstance(parsed, list):
                        return [str(x).strip() for x in parsed if str(x).strip()]
                except Exception:
                    pass
            return [part.strip() for part in s.split(",") if part.strip()]
        return v

    model_config = SettingsConfigDict(
        case_sensitive=True,
        env_file=".env",
        env_file_encoding="utf-8-sig",
        extra="ignore",
    )

settings = Settings()

# Автоматическая подстройка DEBUG
if settings.ENV != "production":
    settings.DEBUG = bool(settings.DEBUG)
else:
    settings.DEBUG = False

# In non-production, enable export endpoint by default unless explicitly disabled
if settings.ENV != "production" and settings.ENABLE_USER_EXPORT is False:
    settings.ENABLE_USER_EXPORT = True

# Защита от небезопасного CORS в production
if settings.ENV == "production" and any(origin.strip() == "*" for origin in settings.BACKEND_CORS_ORIGINS):
    raise ValueError("BACKEND_CORS_ORIGINS cannot contain '*' in production")
