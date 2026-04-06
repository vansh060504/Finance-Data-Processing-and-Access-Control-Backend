from __future__ import annotations
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.database import init_db
from app.routers import auth, dashboard, records, users

@asynccontextmanager
async def lifespan(_: FastAPI):
    init_db()
    yield


def create_app() -> FastAPI:
    app = FastAPI(
        title="Finance Data Processing and Access Control Backend",
        version="1.0.0",
        description=(
            "Backend API for finance record management, dashboard analytics, "
            "and role-based access control."
        ),
        lifespan=lifespan,
    )

    @app.get("/health", tags=["System"])
    def health_check() -> dict:
        return {"status": "ok"}

    app.include_router(auth.router)
    app.include_router(users.router)
    app.include_router(records.router)
    app.include_router(dashboard.router)

    return app


app = create_app()
