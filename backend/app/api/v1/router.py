from fastapi import APIRouter
from app.api.v1.endpoints import auth, lessons, vocabulary, roleplay, gamification, users, path

api_router = APIRouter()

api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(users.router, prefix="/users", tags=["users"])
api_router.include_router(path.router, prefix="/path", tags=["path"]) # Новый маршрутизатор пути
api_router.include_router(lessons.router, prefix="/lessons", tags=["lessons"])
api_router.include_router(vocabulary.router, prefix="/vocabulary", tags=["vocabulary"])
api_router.include_router(roleplay.router, prefix="/roleplay", tags=["roleplay"])
api_router.include_router(gamification.router, prefix="/gamification", tags=["gamification"])
