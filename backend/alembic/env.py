import asyncio
from logging.config import fileConfig

from sqlalchemy import pool
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import async_engine_from_config

from alembic import context

# Импортируем Base и Settings
from app.models.base import Base
# Импортируем все модели, чтобы они зарегистрировались в metadata
from app.models import * 
from app.core.config import settings

# Alembic Config объект даёт доступ к значениям из используемого .ini
config = context.config

# Настраиваем логирование Alembic из ini
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Подменяем sqlalchemy.url в конфиге на DATABASE_URL из settings
config.set_main_option("sqlalchemy.url", settings.DATABASE_URL)

# Metadata моделей для поддержки autogenerate
target_metadata = Base.metadata

# Прочие опции из ini при необходимости можно получать через config.get_main_option(...)


def run_migrations_offline() -> None:
    """Запуск миграций в offline режиме.

    В этом режиме context настраивается только через URL без Engine.
    DBAPI не требуется.

    Вызовы context.execute() печатают SQL в output миграции.

    """
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection: Connection) -> None:
    context.configure(connection=connection, target_metadata=target_metadata)

    with context.begin_transaction():
        context.run_migrations()


async def run_migrations_online() -> None:
    """Запуск миграций в online режиме.

    В этом режиме создаётся Engine и связывается соединение с context.

    """
    connectable = async_engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)

    await connectable.dispose()


if context.is_offline_mode():
    run_migrations_offline()
else:
    asyncio.run(run_migrations_online())
