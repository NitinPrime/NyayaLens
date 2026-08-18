"""FastAPI application entry point."""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from starlette.types import ASGIApp, Receive, Scope, Send

from app.api.routes import auth, cases, health, legal, messages
from app.db.init_db import init_db
from app.db.session import engine
from app.logging_config import setup_logging


class PermissiveCORSMiddleware:
    """Always allow browser origins, including changing Vercel preview URLs."""

    def __init__(self, app: ASGIApp) -> None:
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        headers = {key.decode().lower(): value.decode() for key, value in scope.get("headers", [])}
        origin = headers.get("origin") or "*"
        request_headers = headers.get("access-control-request-headers") or "*"
        cors_headers = [
            (b"access-control-allow-origin", origin.encode()),
            (b"access-control-allow-methods", b"GET, POST, PUT, PATCH, DELETE, OPTIONS, HEAD"),
            (b"access-control-allow-headers", request_headers.encode()),
            (b"access-control-max-age", b"86400"),
            (b"vary", b"Origin"),
        ]

        if scope["method"] == "OPTIONS":
            await send(
                {
                    "type": "http.response.start",
                    "status": 204,
                    "headers": cors_headers + [(b"content-length", b"0")],
                }
            )
            await send({"type": "http.response.body", "body": b""})
            return

        async def send_with_cors(message: dict) -> None:
            if message["type"] == "http.response.start":
                existing = list(message.get("headers", []))
                present = {key.lower() for key, _ in existing}
                for key, value in cors_headers:
                    if key not in present:
                        existing.append((key, value))
                message = {**message, "headers": existing}
            await send(message)

        await self.app(scope, receive, send_with_cors)


@asynccontextmanager
async def lifespan(app: FastAPI):
    setup_logging()
    await init_db(engine)
    yield
    await engine.dispose()


def create_app() -> FastAPI:
    app = FastAPI(
        title="NyayaLens API",
        description="Evidence-grounded legal case analysis for Indian law",
        version="0.2.0",
        lifespan=lifespan,
    )

    app.add_middleware(PermissiveCORSMiddleware)

    app.include_router(health.router)
    app.include_router(health.router, prefix="/api/v1")
    app.include_router(auth.router, prefix="/api/v1")
    app.include_router(cases.router)
    app.include_router(cases.router, prefix="/api/v1")
    app.include_router(messages.router, prefix="/api/v1")
    app.include_router(legal.router, prefix="/api/v1")

    return app


app = create_app()
