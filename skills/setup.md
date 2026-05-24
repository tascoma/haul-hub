# Skill: setup

Bootstrap a new instance of this template from zero: virtual environment, environment file, settings, logging, database, and main entry point.

## Steps

### 0. Virtual environment
Run from the repo root:

```bash
uv venv
uv sync
```

`uv venv` creates `.venv/`. `uv sync` installs all deps from `pyproject.toml`. Never use `pip install` — always `uv add <pkg>` to keep the lockfile in sync.

### 1. Environment file
Copy `.env.example` → `.env` at the repo root and fill in real values. Add any new vars to both files — `.env.example` documents the shape, `.env` holds secrets (gitignored).

### 2. Settings (`backend/app/core/config.py`)
Define a `Settings` class via `pydantic_settings.BaseSettings`. Every env var the app needs is a typed field. Expose one module-level `settings` instance — nothing else reads `os.environ` directly.

```python
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    app_env: str = "development"
    secret_key: str
    host: str = "127.0.0.1"
    port: int = 8000
    # Use str, not list[str] — pydantic-settings JSON-decodes list fields before
    # validators run, which breaks plain comma-separated env values.
    # Split at the call site: settings.allowed_origins.split(",")
    allowed_origins: str = "http://localhost:5173"
    database_url: str
    anthropic_api_key: str
    anthropic_model: str = "claude-sonnet-4-6"
    log_level: str = "INFO"

    model_config = {"env_file": "../.env"}

settings = Settings()
```

### 3. Logging (`backend/app/core/logging.py`)
Implement `configure_logging()` that sets the root log level and format. Call it once from the lifespan in `main.py`. Every module gets its logger via `logging.getLogger(__name__)`.

### 4. Database (`backend/app/databases/`)
Create the async SQLAlchemy engine and `AsyncSessionLocal` factory from `settings.database_url`. Export `get_db` — an async generator that becomes a `Depends()` target.

```python
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from app.core.config import settings

engine = create_async_engine(settings.database_url)
AsyncSessionLocal = async_sessionmaker(engine, expire_on_commit=False)

async def get_db():
    async with AsyncSessionLocal() as session:
        yield session
```

Define `Base = DeclarativeBase()` here too — all ORM models inherit from it.

### 5. Main (`backend/app/main.py`)
Wire everything together:
- Create the `FastAPI` instance.
- Define a `lifespan` context manager: call `configure_logging()` on startup, call `engine.dispose()` on shutdown.
- Include all routers with prefix and tags.
- Configure CORS to allow origins from `settings.allowed_origins.split(",")`.
- Add a `__main__` block so the app runs with `uv run python -m app.main` from `backend/`.

```python
if __name__ == "__main__":
    import uvicorn
    from app.core.config import settings

    uvicorn.run(
        "app.main:app",
        host=settings.host,
        port=settings.port,
        reload=True,
        reload_excludes=["logs/*"],
    )
```

## Verification
After completing setup, run from `backend/`:

```bash
uv run python -m app.main
```

The server should start without errors. Then run `uv run pytest` — all tests should pass (or skip if the test suite is empty).
