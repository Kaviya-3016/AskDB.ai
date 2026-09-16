import asyncio
import os
import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker

# Use isolated in-memory or temp sqlite for testing
os.environ["DATABASE_URL"] = "sqlite+aiosqlite:///./test_app.db"
os.environ["DEMO_DATABASE_URL"] = "sqlite+aiosqlite:///./test_demo.db"

from app.core.database import Base, get_db, get_demo_db
from app.db.models import DemoBase
from app.main import app
from app.db.seed import seed_database

test_engine = create_async_engine("sqlite+aiosqlite:///./test_app.db", echo=False)
TestSessionLocal = async_sessionmaker(bind=test_engine, class_=AsyncSession, expire_on_commit=False)

test_demo_engine = create_async_engine("sqlite+aiosqlite:///./test_demo.db", echo=False)
TestDemoSessionLocal = async_sessionmaker(bind=test_demo_engine, class_=AsyncSession, expire_on_commit=False)


@pytest_asyncio.fixture(scope="session", autouse=True)
async def init_test_db():
    await seed_database()
    yield
    # Cleanup test databases after tests
    for db_file in ["test_app.db", "test_demo.db"]:
        if os.path.exists(db_file):
            try:
                os.remove(db_file)
            except Exception:
                pass


@pytest_asyncio.fixture
async def client():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


@pytest_asyncio.fixture
async def admin_auth_token(client: AsyncClient):
    login_resp = await client.post(
        "/api/auth/login",
        json={"email": "admin@company.com", "password": "Admin@123456"},
    )
    data = login_resp.json()
    return data["access_token"]


@pytest_asyncio.fixture
async def analyst_auth_token(client: AsyncClient):
    login_resp = await client.post(
        "/api/auth/login",
        json={"email": "analyst@company.com", "password": "Analyst@123456"},
    )
    data = login_resp.json()
    return data["access_token"]
