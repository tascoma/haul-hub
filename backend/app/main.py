import logging
from contextlib import asynccontextmanager
from pathlib import Path
from typing import AsyncIterator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from app.core.config import settings
from app.core.logging import configure_logging
from app.databases import engine
from app.services.storage import UPLOAD_ROOT

FRONTEND_DIST = Path(__file__).resolve().parent.parent.parent / "frontend" / "dist"

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncIterator[None]:
    configure_logging()
    logger.info("Starting up (env=%s)", settings.app_env)
    yield
    logger.info("Shutting down")
    await engine.dispose()


app = FastAPI(
    title="haul-hub",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins.split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health", include_in_schema=False)
async def health_check() -> dict:
    return {"status": "ok"}


from app.routes import auth as auth_routes
from app.routes import loads as loads_routes
from app.routes import me as me_routes
from app.routes import webhooks as webhook_routes

app.include_router(auth_routes.router, prefix="/api/auth", tags=["auth"])
app.include_router(me_routes.router, prefix="/api/me", tags=["me"])
app.include_router(loads_routes.router, prefix="/api/loads", tags=["loads"])
app.include_router(webhook_routes.router, prefix="/api/webhooks", tags=["webhooks"])

UPLOAD_ROOT.mkdir(parents=True, exist_ok=True)
app.mount("/uploads", StaticFiles(directory=UPLOAD_ROOT), name="uploads")

if FRONTEND_DIST.exists():
    @app.get("/{full_path:path}", include_in_schema=False)
    async def serve_frontend(full_path: str) -> FileResponse:
        target = FRONTEND_DIST / full_path
        if target.is_file():
            return FileResponse(target)
        return FileResponse(FRONTEND_DIST / "index.html")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host=settings.host,
        port=settings.port,
        reload=True,
        reload_excludes=["logs/*"],
    )
