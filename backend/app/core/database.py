from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import declarative_base
from app.core.config import settings

# Primary Application Database Engine
connect_args = {"check_same_thread": False} if "sqlite" in settings.DATABASE_URL else {}
engine = create_async_engine(
    settings.DATABASE_URL,
    echo=False,
    connect_args=connect_args,
)

AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)

# Target Demo Database Engine (for sandboxed query execution)
demo_connect_args = {"check_same_thread": False} if "sqlite" in settings.DEMO_DATABASE_URL else {}
demo_engine = create_async_engine(
    settings.DEMO_DATABASE_URL,
    echo=False,
    connect_args=demo_connect_args,
)

DemoAsyncSessionLocal = async_sessionmaker(
    bind=demo_engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)

Base = declarative_base()


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Dependency for obtaining async application database session."""
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def get_demo_db() -> AsyncGenerator[AsyncSession, None]:
    """Dependency for obtaining demo sandbox database session."""
    async with DemoAsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()
