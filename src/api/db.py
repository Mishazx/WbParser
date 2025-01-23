from typing import AsyncGenerator
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.ext.declarative import declarative_base

SYNC_PROTOCOL = "postgresql"
ASYNC_PROTOCOL = "postgresql+asyncpg"

DATABASE_URL = "user:password@db:5432/database"

SYNC_DATABASE_URL = f"{SYNC_PROTOCOL}://{DATABASE_URL}"
ASYNC_DATABASE_URL = f"{ASYNC_PROTOCOL}://{DATABASE_URL}"

SyncEngine = create_engine(SYNC_DATABASE_URL)
AsyncEngine = create_async_engine(ASYNC_DATABASE_URL, echo=True)
AsyncSessionLocal = async_sessionmaker(
    bind=AsyncEngine,
    class_=AsyncSession,
    expire_on_commit=False
)
SyncSessionLocal = sessionmaker(
    bind=SyncEngine,
    class_=Session,
    expire_on_commit=False
)

Base = declarative_base()


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()