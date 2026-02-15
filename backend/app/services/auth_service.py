from sqlalchemy.ext.asyncio import AsyncSession
from app.schemas.user import UserCreate
from app.core.security import get_password_hash, verify_password
from app.repositories.user import UserRepository
from app.models.user import User

class AuthService:
    @staticmethod
    async def get_user_by_username(db: AsyncSession, username: str):
        repo = UserRepository(db)
        return await repo.get_by_username(username)

    @staticmethod
    async def get_user_by_username_or_email(db: AsyncSession, identifier: str):
        repo = UserRepository(db)
        return await repo.get_by_username_or_email(identifier)

    @staticmethod
    async def create_user(db: AsyncSession, user_in: UserCreate):
        repo = UserRepository(db)
        hashed_password = get_password_hash(user_in.password)
        db_user = User(
            username=user_in.username,
            email=user_in.email,
            hashed_password=hashed_password,
            language_levels={}
        )
        return await repo.create(db_user)

    @staticmethod
    async def authenticate_user(db: AsyncSession, username: str, password: str):
        # Аутентификация пользователя по имени пользователя или email
        user = await AuthService.get_user_by_username_or_email(db, username)
        if not user:
            return None
        if not verify_password(password, user.hashed_password):
            return None
        return user
