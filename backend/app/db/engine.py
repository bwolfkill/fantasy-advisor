from core.config import settings
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

engine = create_async_engine(
    settings.DATABASE_URL,
    pool_size=5,
    max_overflow=10,
    echo=settings.ENVIRONMENT == "dev",
)

AsyncSessionLocal = async_sessionmaker(bind=engine, expire_on_commit=False)
