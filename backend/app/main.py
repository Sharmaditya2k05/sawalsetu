"""SawalSetu API – RAG over MargBooks data."""
from __future__ import annotations

import logging
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from .api.routes import router
from .config import settings
from .rag.pipeline import Pipeline

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")
log = logging.getLogger("sawalsetu")

FRONTEND_DIST = Path(__file__).resolve().parents[2] / "frontend" / "dist"


@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.pipeline = Pipeline(settings)
    status = app.state.pipeline.status()
    log.info("mode=%s llm=%s embeddings=%s documents=%d", status["mode"], status["llm"]["provider"],
             status["embeddings"], status["documents"])
    if not status["ready"] and settings.margbooks_mode != "live":
        log.info("no index found – running initial demo sync")
        await app.state.pipeline.sync()
    yield


app = FastAPI(title="SawalSetu", version="0.1.0", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(router)

if FRONTEND_DIST.exists():  # serve the built SPA in production
    app.mount("/", StaticFiles(directory=FRONTEND_DIST, html=True), name="frontend")
