from collections.abc import AsyncIterator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from app.core.config import settings

# Supabase's transaction pooler (PgBouncer on :6543) doesn't support the
# server-side prepared statements psycopg issues by default; under concurrency
# they collide ("prepared statement _pg3_0 already exists"). Disable them for
# psycopg connections. Left untouched for SQLite (tests) and other drivers.
_connect_args: dict = {}
if settings.database_url.startswith("postgresql+psycopg"):
    _connect_args["prepare_threshold"] = None

engine = create_async_engine(
    settings.database_url,
    echo=False,
    future=True,
    pool_pre_ping=True,
    connect_args=_connect_args,
)

AsyncSessionLocal = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)


class Base(DeclarativeBase):
    pass


async def get_db() -> AsyncIterator[AsyncSession]:
    async with AsyncSessionLocal() as session:
        yield session
