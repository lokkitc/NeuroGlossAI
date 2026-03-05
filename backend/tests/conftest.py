import os
import sys
from pathlib import Path
from typing import AsyncGenerator, Any

import pytest
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import AsyncSession
import sqlalchemy as sa
from sqlalchemy import select


# Ensure project root is importable (so `import app` works under pytest).
_ROOT = Path(__file__).resolve().parents[1]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

# Ensure settings can load at import time.
os.environ.setdefault("ENV", "test")
os.environ.setdefault("DEBUG", "false")
os.environ.setdefault("LOG_LEVEL", "WARNING")
os.environ.setdefault("SECRET_KEY", "test-secret-key")

# Force tests to use SQLite even if the outer environment sets DATABASE_URL (e.g. Railway).
os.environ["DATABASE_URL"] = "sqlite+aiosqlite:///./data/test_api.db"

os.makedirs("./data", exist_ok=True)


@pytest.fixture(scope="session")
def anyio_backend():
    return "asyncio"


@pytest.fixture(scope="session")
def app() -> Any:
    from app.main import app as fastapi_app

    limiter = getattr(fastapi_app.state, "limiter", None)
    if limiter is not None:
        try:
            limiter.enabled = False
        except Exception:
            pass

    return fastapi_app


@pytest.fixture(scope="session")
def async_sessionmaker():
    from app.core.database import AsyncSessionLocal

    return AsyncSessionLocal


@pytest.fixture(autouse=True)
async def _db_schema(async_sessionmaker) -> AsyncGenerator[None, None]:
    # Create all tables for tests using SQLAlchemy metadata (not Alembic).
    from app.features.common.db import Base
    from app.core.database import engine

    # Import all model modules so they register tables in Base.metadata.
    from app.features.achievements import models as _achievements_models  # noqa: F401
    from app.features.ai import models as _ai_models  # noqa: F401
    from app.features.auth import models as _auth_models  # noqa: F401
    from app.features.characters import models as _characters_models  # noqa: F401
    from app.features.chat import models as _chat_models  # noqa: F401
    from app.features.memory import models as _memory_models  # noqa: F401
    from app.features.posts import models as _posts_models  # noqa: F401
    from app.features.rooms import models as _rooms_models  # noqa: F401
    from app.features.subscriptions import models as _subscriptions_models  # noqa: F401
    from app.features.themes import models as _themes_models  # noqa: F401
    from app.features.uploads import models as _uploads_models  # noqa: F401
    from app.features.users import models as _users_models  # noqa: F401

    async with engine.begin() as conn:
        # Reset schema for each test without relying on SQLAlchemy drop_all(),
        # which can fail on cyclic foreign keys.
        if conn.dialect.name == "sqlite":
            await conn.execute(sa.text("PRAGMA foreign_keys=OFF"))

        # Drop all tables explicitly (reverse order gives best effort).
        for table in reversed(list(Base.metadata.tables.values())):
            await conn.execute(sa.text(f'DROP TABLE IF EXISTS "{table.name}"'))

        if conn.dialect.name == "sqlite":
            await conn.execute(sa.text("PRAGMA foreign_keys=ON"))

        await conn.run_sync(Base.metadata.create_all)

    yield


@pytest.fixture
async def db(async_sessionmaker) -> AsyncGenerator[AsyncSession, None]:
    async with async_sessionmaker() as session:
        yield session


@pytest.fixture
async def client(app) -> AsyncGenerator[AsyncClient, None]:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        yield c


async def _register_user(client: AsyncClient, *, username: str, email: str, password: str) -> dict:
    r = await client.post(
        "/api/v1/auth/register",
        json={"username": username, "email": email, "password": password},
        headers={"X-Session-Id": "test", "X-Device-Id": "test"},
    )
    assert r.status_code in {200, 400}, r.text
    return r.json() if r.status_code == 200 else {}


async def _login(client: AsyncClient, *, username: str, password: str) -> dict:
    r = await client.post(
        "/api/v1/auth/login",
        data={"username": username, "password": password},
        headers={
            "Content-Type": "application/x-www-form-urlencoded",
            "X-Session-Id": "test",
            "X-Device-Id": "test",
        },
    )
    assert r.status_code == 200, r.text
    return r.json()


@pytest.fixture
async def user_tokens(client: AsyncClient) -> dict:
    username = "user1"
    email = "user1@example.com"
    password = "password123"

    await _register_user(client, username=username, email=email, password=password)
    return await _login(client, username=username, password=password)


@pytest.fixture
async def user_auth_headers(user_tokens: dict) -> dict[str, str]:
    return {"Authorization": f"Bearer {user_tokens['access_token']}"}


@pytest.fixture
async def admin_tokens(client: AsyncClient, db: AsyncSession) -> dict:
    username = "admin1"
    email = "admin1@example.com"
    password = "password123"

    await _register_user(client, username=username, email=email, password=password)

    from app.features.users.models import User

    res = await db.execute(select(User).where(User.username == username))
    u = res.scalars().first()
    assert u is not None
    u.is_admin = True
    db.add(u)
    await db.commit()

    return await _login(client, username=username, password=password)


@pytest.fixture
async def admin_auth_headers(admin_tokens: dict) -> dict[str, str]:
    return {"Authorization": f"Bearer {admin_tokens['access_token']}"}
