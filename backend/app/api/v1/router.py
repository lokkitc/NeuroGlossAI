from fastapi import APIRouter
from app.api.v1.endpoints import auth, lessons, vocabulary, roleplay, gamification, users, path, admin
from app.api.v1.endpoints import characters, rooms, chat, memory, chat_learning
from app.api.v1.endpoints import uploads
from app.api.v1.endpoints import posts
from app.api.v1.endpoints import themes
from app.core.config import settings

api_router = APIRouter()

api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(users.router, prefix="/users", tags=["users"])

if settings.ENABLE_LEGACY_PATH:
    api_router.include_router(path.router, prefix="/path", tags=["path"])          
if settings.ENABLE_LEGACY_LESSONS:
    api_router.include_router(lessons.router, prefix="/lessons", tags=["lessons"])          
if settings.ENABLE_LEGACY_VOCABULARY:
    api_router.include_router(vocabulary.router, prefix="/vocabulary", tags=["vocabulary"])          
if settings.ENABLE_LEGACY_ROLEPLAY:
    api_router.include_router(roleplay.router, prefix="/roleplay", tags=["roleplay"])          
if settings.ENABLE_LEGACY_GAMIFICATION:
    api_router.include_router(gamification.router, prefix="/gamification", tags=["gamification"])          
if settings.ENABLE_LEGACY_ADMIN:
    api_router.include_router(admin.router, prefix="/admin", tags=["admin"])

api_router.include_router(characters.router, prefix="/characters", tags=["characters"])
api_router.include_router(rooms.router, prefix="/rooms", tags=["rooms"])
api_router.include_router(chat.router, prefix="/chat", tags=["chat"])
api_router.include_router(memory.router, prefix="/memory", tags=["memory"])
api_router.include_router(chat_learning.router, prefix="/chat-learning", tags=["chat_learning"])
api_router.include_router(uploads.router, prefix="/uploads", tags=["uploads"])
api_router.include_router(posts.router, prefix="/posts", tags=["posts"])
api_router.include_router(themes.router, prefix="/themes", tags=["themes"])
