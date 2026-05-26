"""Shared fixtures for the backend test suite.

Tests run against on-disk SQLite (per-test drop_all/create_all). The production
schema lives in Postgres + PostGIS via Supabase, but the geo-specific features
(PostGIS `geom` columns, GIST/trigger logic) are intentionally absent from the
ORM model so the test database can be SQLite. Postgres-only behavior is
exercised by migrations against a live Supabase branch, not by this suite.
"""

import os
from collections.abc import AsyncIterator
from pathlib import Path

import pytest

TEST_DB_PATH = Path(__file__).resolve().parent / "test.db"
os.environ["DATABASE_URL"] = f"sqlite+aiosqlite:///{TEST_DB_PATH}"
os.environ.setdefault("SECRET_KEY", "test-secret-key-at-least-32-bytes-long-for-hs256")
os.environ.pop("STRIPE_SECRET_KEY", None)
os.environ.pop("STRIPE_WEBHOOK_SECRET", None)

from httpx import ASGITransport, AsyncClient  # noqa: E402

import app.models  # noqa: E402,F401  -- register mappers on Base.metadata
from app.databases import Base, engine  # noqa: E402
from app.main import app  # noqa: E402


@pytest.fixture(autouse=True)
async def _fresh_db() -> AsyncIterator[None]:
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest.fixture
async def client() -> AsyncIterator[AsyncClient]:
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        yield c
