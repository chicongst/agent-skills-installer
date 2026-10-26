from sqlalchemy import MetaData, text
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from todo_api.settings import PostgresStorage

NAMING_CONVENTION = {
    "ix": "ix_%(table_name)s_%(column_0_N_name)s",
    "uq": "uq_%(table_name)s_%(column_0_N_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s",
}


class Base(DeclarativeBase):
    metadata = MetaData(naming_convention=NAMING_CONVENTION)


def create_engine(storage: PostgresStorage) -> AsyncEngine:
    return create_async_engine(
        storage.database_url.get_secret_value(),
        pool_size=storage.pool_size,
        max_overflow=storage.max_overflow,
        pool_timeout=storage.pool_timeout_seconds,
        pool_pre_ping=True,
        connect_args={
            "timeout": storage.connect_timeout_seconds,
            "command_timeout": storage.statement_timeout_seconds,
            "server_settings": {"application_name": "todo-api"},
        },
    )


def create_session_factory(engine: AsyncEngine) -> async_sessionmaker[AsyncSession]:
    return async_sessionmaker(engine, expire_on_commit=False)


async def ping(engine: AsyncEngine) -> None:
    async with engine.connect() as connection:
        await connection.execute(text("SELECT 1"))
