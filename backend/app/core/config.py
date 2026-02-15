from typing import List
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

# Защита от небезопасного CORS в production
if settings.ENV == "production" and any(origin.strip() == "*" for origin in settings.BACKEND_CORS_ORIGINS):
    raise ValueError("BACKEND_CORS_ORIGINS cannot contain '*' in production")
