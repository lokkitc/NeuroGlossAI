from fastapi import FastAPI, Request, status, HTTPException
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
import uuid
import time

from app.core.config import settings
from app.api.v1.router import api_router
from app.core.exceptions import NeuroGlossException
from app.core.rate_limit import limiter
from app.core.events.base import event_bus, LevelCompletedEvent
from app.core.events.listeners import XPListener, AchievementListener
import logging

# Настройка логирования
logging.basicConfig(level=getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO))
logger = logging.getLogger(__name__)

# Регистрация слушателей событий
event_bus.subscribe(LevelCompletedEvent, XPListener())
event_bus.subscribe(LevelCompletedEvent, AchievementListener())

app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_V1_STR}/openapi.json"
)


@app.middleware("http")
async def request_id_middleware(request: Request, call_next):
    request_id = request.headers.get("X-Request-Id") or str(uuid.uuid4())
    request.state.request_id = request_id
    start = time.perf_counter()
    response = await call_next(request)
    response.headers["X-Request-Id"] = request_id
    duration_ms = int((time.perf_counter() - start) * 1000)
    logger.info(
        "%s %s -> %s (%sms) request_id=%s",
        request.method,
        request.url.path,
        response.status_code,
        duration_ms,
        request_id,
    )
    return response

# Прикрепление ограничителя к состоянию приложения, чтобы зависимости могли получить к нему доступ
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Глобальный обработчик исключений
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    request_id = getattr(request.state, "request_id", None)
    logger.error(f"Global exception. request_id={request_id}", exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "code": "internal_error",
            "message": "Internal Server Error",
            "request_id": request_id,
        },
    )

@app.exception_handler(NeuroGlossException)
async def neurogloss_exception_handler(request: Request, exc: NeuroGlossException):
    request_id = getattr(request.state, "request_id", None)
    message = exc.detail
    if settings.ENV == "production" and exc.status_code >= 500:
        message = "Internal Server Error"
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "code": "neurogloss_error",
            "message": message,
            "request_id": request_id,
        },
    )


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    request_id = getattr(request.state, "request_id", None)
    message = exc.detail
    if settings.ENV == "production" and exc.status_code >= 500:
        message = "Internal Server Error"
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "code": "http_error",
            "message": message,
            "request_id": request_id,
        },
        headers=getattr(exc, "headers", None),
    )

# Установка всех источников, разрешенных CORS
if settings.BACKEND_CORS_ORIGINS:
    cors_origins = [str(origin).strip() for origin in settings.BACKEND_CORS_ORIGINS]
    allow_credentials = True
    # Нельзя сочетать allow_credentials=True и allow_origins=['*']
    if any(origin == "*" for origin in cors_origins):
        allow_credentials = False
    app.add_middleware(
        CORSMiddleware,
        allow_origins=cors_origins,
        allow_credentials=allow_credentials,
        allow_methods=["*"],
        allow_headers=["*"],
    )

app.include_router(api_router, prefix=settings.API_V1_STR)

@app.get("/")
def root():
    return {"message": "Welcome to NeuroGlossAI API"}
