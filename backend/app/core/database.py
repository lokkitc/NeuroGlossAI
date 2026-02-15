from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import DeclarativeBase
from app.core.config import settings

# Создание асинхронного движка
# Нам нужно обработать потенциальные различия в строках подключения SQLite и Postgres, если потребуется,
# но обычно sqlalchemy нормально обрабатывает 'sqlite+aiosqlite' и 'postgresql+asyncpg'.
engine = create_async_engine(
    settings.DATABASE_URL,
    echo=False, # Установите True, чтобы видеть SQL-запросы в логах
    future=True
)

# Создание фабрики сессий
AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False
)

# Внедрение зависимостей для API
async def get_db():
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()
