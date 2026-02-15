"""Pytest фикстуры для backend.

Содержит:
- in-memory SQLite для изолированных тестов
- AsyncClient с переопределённой зависимостью get_db
"""

import pytest
import pytest_asyncio
import asyncio
from typing import AsyncGenerator
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

# Импорты должны работать при запуске из разных директорий
try:
    from app.main import app
    from app.api.deps import get_db
    from app.models.base import Base
    from app.services.ai_service import ai_service
except ImportError:
    import sys
    import os
    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from app.main import app
    from app.api.deps import get_db
    from app.models.base import Base
    from app.services.ai_service import ai_service

# Используем in-memory SQLite для тестов
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"

engine = create_async_engine(
    TEST_DATABASE_URL, 
    connect_args={"check_same_thread": False}, 
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)

@pytest_asyncio.fixture(scope="function")
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    """Создаёт чистую БД для каждой тестовой функции."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    async with TestingSessionLocal() as session:
        yield session
    
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

@pytest_asyncio.fixture(scope="function")
async def async_client(db_session: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    """Создаёт тестовый клиент с переопределённой зависимостью БД."""
    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        yield c
    
    app.dependency_overrides.clear()

@pytest.fixture
def normal_user_token_headers(async_client):
    """
    Хелпер-фикстура для auth headers.
    Так как для register/login нужны async вызовы, эту логику чаще проще держать внутри самих тестов
    или выделять в отдельную async-фикстуру.
    """
    return {}  # Тесты сами пройдут auth-flow при необходимости

# Не используем autouse mock, т.к. разным тестам нужны разные моки (Path vs Lesson).
# Тесты объявляют свои mock-фикстуры.
