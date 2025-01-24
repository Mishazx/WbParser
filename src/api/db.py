import asyncio
from typing import AsyncGenerator
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.exc import OperationalError

SYNC_PROTOCOL = "postgresql"
ASYNC_PROTOCOL = "postgresql+asyncpg"

DATABASE_URL = "postgres:postgres@db:5432/database"

SYNC_DATABASE_URL = f"{SYNC_PROTOCOL}://{DATABASE_URL}"
ASYNC_DATABASE_URL = f"{ASYNC_PROTOCOL}://{DATABASE_URL}"

SyncEngine = create_engine(SYNC_DATABASE_URL)
AsyncEngine = create_async_engine(ASYNC_DATABASE_URL)
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
            
            
async def connect_with_retries(max_retries: int = 5, delay: int = 2):
    for attempt in range(max_retries):
        try:
            async with AsyncEngine.begin() as conn:
                await conn.run_sync(Base.metadata.create_all)
            return  # Успешное подключение, выходим из функции
        except OperationalError as e:
            print(f"Ошибка подключения к базе данных: {e}. Попытка {attempt + 1} из {max_retries}.")
            await asyncio.sleep(delay)  # Ждем перед следующей попыткой
    raise Exception("Не удалось подключиться к базе данных после нескольких попыток.")