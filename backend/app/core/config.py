import json
from typing import List

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    PROJECT_NAME: str = "NeuroGlossAI"
    API_V1_STR: str = "/api/v1"

               
    ENV: str = "development"                                      
    DEBUG: bool = False
    LOG_LEVEL: str = "INFO"
    
                 
    DATABASE_URL: str
    
                  
    SECRET_KEY: str
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 30
    ALGORITHM: str = "HS256"

                         
    ENABLE_USER_EXPORT: bool = False
    
        
    AI_ENABLED: bool = True
    GROQ_API_KEY: str | None = None
    GROQ_FALLBACK_MODELS: List[str] = ["llama-3.1-8b-instant", "llama-3.3-70b-versatile"]
    AI_CIRCUIT_BREAKER_FAIL_THRESHOLD: int = 3
    AI_CIRCUIT_BREAKER_OPEN_SECONDS: int = 60

    AI_REQUEST_TIMEOUT_SECONDS: int = 30
    AI_MAX_PROMPT_CHARS: int = 20000
    AI_MAX_RESPONSE_CHARS: int = 200000

    TOPIC_RETRIEVAL_ENABLED: bool = False
    TOPIC_RETRIEVAL_WIKI_LANG: str = "ru"
    TOPIC_RETRIEVAL_TIMEOUT_SECONDS: int = 8
    TOPIC_RETRIEVAL_CACHE_TTL_SECONDS: int = 86400
    TOPIC_RETRIEVAL_MAX_ENTITIES: int = 20

    TOPIC_RETRIEVAL_FANDOM_ENABLED: bool = False
    TOPIC_RETRIEVAL_FANDOM_MAX_RESULTS: int = 5
    TOPIC_RETRIEVAL_FANDOM_ROSTER_MAX: int = 80

    AI_TEMPERATURE_TEXT: float = 0.6
    AI_TEMPERATURE_JSON: float = 0.2
    AI_TEMPERATURE_REPAIR: float = 0.1
    
                
    GEMINI_API_KEY: str = ""

          
    BACKEND_CORS_ORIGINS: List[str] = ["http://localhost:5173", "http://localhost:3000"]

                                                      
    CHAT_LEARNING_ENABLED: bool = True
    CHAT_LEARNING_EVERY_USER_TURNS: int = 10
    CHAT_LEARNING_TURN_WINDOW: int = 80

                                                                  
    ENABLE_LEGACY_PATH: bool = False
    ENABLE_LEGACY_LESSONS: bool = False
    ENABLE_LEGACY_VOCABULARY: bool = False
    ENABLE_LEGACY_ROLEPLAY: bool = False
    ENABLE_LEGACY_GAMIFICATION: bool = False
    ENABLE_LEGACY_ADMIN: bool = False

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

                                 
if settings.ENV != "production":
    settings.DEBUG = bool(settings.DEBUG)
else:
    settings.DEBUG = False

                                                                                 
if settings.ENV != "production" and settings.ENABLE_USER_EXPORT is False:
    settings.ENABLE_USER_EXPORT = True

                                           
if settings.ENV == "production" and any(origin.strip() == "*" for origin in settings.BACKEND_CORS_ORIGINS):
    raise ValueError("BACKEND_CORS_ORIGINS cannot contain '*' in production")
