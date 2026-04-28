from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.core.config import settings

engine = create_async_engine(
    settings.database_url,
    pool_size=5,
    max_overflow=10,
    echo=settings.environment == "development",
)

AsyncSessionLocal = async_sessionmaker(bind=engine, expire_on_commit=False)
