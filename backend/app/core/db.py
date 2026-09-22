"""Asynchronous PostgreSQL database setup and session management using SQLModel and asyncpg."""

from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlmodel.ext.asyncio.session import AsyncSession

from app.core.config import settings

# Initialize AsyncEngine loading connection string from app.core.config.settings
engine: AsyncEngine = create_async_engine(
    settings.DATABASE_URL,
    echo=settings.DEBUG,
    future=True,
)

# Async session factory bound to AsyncEngine
async_session_maker = sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
)


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    """Dependency for FastAPI endpoints yielding an AsyncSession instance."""
    async with async_session_maker() as session:
        yield session
