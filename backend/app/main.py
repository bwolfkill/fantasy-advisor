from typing import Annotated

from api.router import api_v1_router
from core.config import settings
from db.session import get_db
from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.ext.asyncio import AsyncSession


def create_app() -> FastAPI:
    app = FastAPI(
        title="Fantasy Advisor API",
        version="0.1.0",
        docs_url="/docs",
        redoc_url="/redoc",
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(api_v1_router, prefix="/api/v1")

    @app.get(
        "/health",
    )
    async def health(db: Annotated[AsyncSession, Depends(get_db)]):
        try:
            await db.execute("SELECT 1")
            db_status = "healthy"
        except Exception:
            db_status = "unhealthy"
        return {"status": "healthy", "db_status": db_status}

    return app


app = create_app()
