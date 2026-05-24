from __future__ import annotations

import logging
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from app.core.database import configure_logging
from app.core.exceptions import register_exception_handlers
from app.models import (
    MetaPromptTemplate,
    ModelConfig,
    PersonaTrait,
    PostprocessRule,
    Project,
    Prompt,
)
from app.api import generate, history, models, personas, postprocess, projects, templates

logger = logging.getLogger(__name__)

_STATIC_DIR = Path(__file__).resolve().parent / "app" / "static"
_INDEX_HTML = _STATIC_DIR / "index.html"


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Prompt Factory starting up...")
    yield
    logger.info("Prompt Factory shutting down...")


app = FastAPI(
    title="Prompt Factory",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

configure_logging()
register_exception_handlers(app)

app.include_router(projects.router)
app.include_router(generate.router)
app.include_router(personas.router)
app.include_router(templates.router)
app.include_router(postprocess.router)
app.include_router(models.router)
app.include_router(history.router)

try:
    app.mount(
        "/assets",
        StaticFiles(directory=str(_STATIC_DIR / "assets")),
        name="static_assets",
    )
except Exception:
    logger.warning("Static assets directory not found, skipping mount")


@app.get("/{full_path:path}")
async def spa_catchall(full_path: str):
    if full_path.startswith("api"):
        return JSONResponse(status_code=404, content={"detail": "Not Found"})
    if _INDEX_HTML.exists():
        return FileResponse(str(_INDEX_HTML))
    return JSONResponse(status_code=404, content={"detail": "Not Found"})
