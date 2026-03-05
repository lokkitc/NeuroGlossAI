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

    RATE_LIMIT_TRUST_PROXY: bool = False
    
                 
    DATABASE_URL: str
    
                  
    SECRET_KEY: str
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 30
    ALGORITHM: str = "HS256"

    JWT_ISSUER: str | None = None
    JWT_AUDIENCE: str | None = None

                         
    ENABLE_USER_EXPORT: bool = False
    
        
    AI_ENABLED: bool = True
    GROQ_API_KEY: str | None = None
    GROQ_FALLBACK_MODELS: List[str] = ["llama-3.1-8b-instant", "llama-3.3-70b-versatile"]
    AI_CIRCUIT_BREAKER_FAIL_THRESHOLD: int = 3
    AI_CIRCUIT_BREAKER_OPEN_SECONDS: int = 60

    AI_REQUEST_TIMEOUT_SECONDS: int = 30
    AI_MAX_PROMPT_CHARS: int = 20000
    AI_MAX_RESPONSE_CHARS: int = 200000

    AI_TEMPERATURE_TEXT: float = 0.6
    AI_TEMPERATURE_JSON: float = 0.2
    AI_TEMPERATURE_REPAIR: float = 0.1

          
    BACKEND_CORS_ORIGINS: List[str] = ["http://localhost:5173", "http://localhost:3000"]

    CLOUDINARY_CLOUD_NAME: str | None = None
    CLOUDINARY_API_KEY: str | None = None
    CLOUDINARY_API_SECRET: str | None = None
    UPLOAD_PROVIDER: str = "cloudinary"  # cloudinary | s3
    UPLOADS_ENABLED: bool = True
    UPLOAD_MAX_BYTES: int = 5_000_000

    S3_ENDPOINT_URL: str | None = None
    S3_REGION: str = "auto"
    S3_BUCKET_NAME: str | None = None
    S3_ACCESS_KEY_ID: str | None = None
    S3_SECRET_ACCESS_KEY: str | None = None
    S3_PUBLIC_BASE_URL: str | None = None
    S3_USE_VIRTUAL_HOSTED_STYLE: bool = True

    # Uploads privacy defaults. If S3_OBJECT_ACL is empty/None, objects are uploaded privately.
    # You can set it to "public-read" if you explicitly want public objects.
    S3_OBJECT_ACL: str | None = None
    S3_RETURN_PRESIGNED_URL: bool = True
    S3_PRESIGNED_URL_EXPIRES_SECONDS: int = 3600

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
