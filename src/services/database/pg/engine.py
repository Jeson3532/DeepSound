from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy import text

from src.services.database.pg.config import DBConfig

cfg = DBConfig()

engine = create_async_engine(
    cfg.get_url(driver='asyncpg'),
    pool_size=cfg.POOL_SIZE,
    max_overflow=cfg.POOL_OVERFLOW,
    pool_timeout=cfg.POOL_TIMEOUT
)
session_fabric = async_sessionmaker(engine, autoflush=False, expire_on_commit=False)


async def get_session() -> AsyncSession:
    async with session_fabric() as session:
        yield session
