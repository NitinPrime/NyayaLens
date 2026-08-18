"""FastAPI application entry point."""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import auth, cases, health, legal, messages
from app.config import get_settings
from app.db.init_db import init_db
from app.db.session import engine
from app.logging_config import setup_logging


@asynccontextmanager
async def lifespan(app: FastAPI):
    setup_logging()
    await init_db(engine)
    yield
    await engine.dispose()


def create_app() -> FastAPI:
    settings = get_settings()

    app = FastAPI(
        title="NyayaLens API",
        description="Evidence-grounded legal case analysis for Indian law",
        version="0.2.0",
        lifespan=lifespan,
    )

    # Browsers reject allow_origins=["*"] together with allow_credentials=True.
    # Vercel preview URLs change every deploy, so allow any vercel.app origin.
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_origin_regex=r"https://.*\.vercel\.app",
        allow_credentials=False,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(health.router)
    app.include_router(health.router, prefix="/api/v1")
    app.include_router(auth.router, prefix="/api/v1")
    app.include_router(cases.router)
    app.include_router(cases.router, prefix="/api/v1")
    app.include_router(messages.router, prefix="/api/v1")
    app.include_router(legal.router, prefix="/api/v1")

    return app


app = create_app()
