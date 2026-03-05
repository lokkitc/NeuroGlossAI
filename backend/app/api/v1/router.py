from fastapi import APIRouter
from app.api.v1.endpoints import auth, users, public
from app.api.v1.endpoints import characters, rooms, chat, memory
from app.api.v1.endpoints import uploads
from app.api.v1.endpoints import posts
from app.api.v1.endpoints import themes
from app.api.v1.endpoints import subscriptions
from app.api.v1.endpoints import achievements

api_router = APIRouter()

api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(users.router, prefix="/users", tags=["users"])
api_router.include_router(public.router, prefix="/public", tags=["public"])

api_router.include_router(characters.router, prefix="/characters", tags=["characters"])
api_router.include_router(rooms.router, prefix="/rooms", tags=["rooms"])
api_router.include_router(chat.router, prefix="/chat", tags=["chat"])
api_router.include_router(memory.router, prefix="/memory", tags=["memory"])
api_router.include_router(uploads.router, prefix="/uploads", tags=["uploads"])
api_router.include_router(posts.router, prefix="/posts", tags=["posts"])
api_router.include_router(themes.router, prefix="/themes", tags=["themes"])
api_router.include_router(subscriptions.router, prefix="/subscriptions", tags=["subscriptions"])
api_router.include_router(achievements.router, prefix="/achievements", tags=["achievements"])
