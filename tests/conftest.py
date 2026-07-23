import os
import pytest
from collections.abc import AsyncGenerator

import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.engine import make_url
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

import app.models  # noqa: F401
from app.core.config import settings
from app.db.base import Base
from app.db.session import get_db
from app.main import app


TEST_DATABASE_URL_ASYNC = os.getenv(
    "TEST_DATABASE_URL_ASYNC",
    settings.TEST_DATABASE_URL_ASYNC,
)

test_database_name = make_url(TEST_DATABASE_URL_ASYNC).database

if (
    test_database_name == settings.POSTGRES_DB
    or not test_database_name
    or not test_database_name.endswith("_test")
):
    raise RuntimeError(
        "Tests must use a separate database whose name ends with '_test'. "
        f"Received database: {test_database_name!r}"
    )

test_engine = create_async_engine(
    TEST_DATABASE_URL_ASYNC,
    echo=False,
    pool_pre_ping=True,
)

TestingSessionLocal = async_sessionmaker(
    bind=test_engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


@pytest_asyncio.fixture(scope="session", autouse=True)
async def prepare_test_database() -> AsyncGenerator[None, None]:
    async with test_engine.begin() as connection:
        await connection.run_sync(Base.metadata.drop_all)
        await connection.run_sync(Base.metadata.create_all)

    yield

    async with test_engine.begin() as connection:
        await connection.run_sync(Base.metadata.drop_all)


@pytest_asyncio.fixture(autouse=True)
async def clean_tables() -> AsyncGenerator[None, None]:
    async with test_engine.begin() as connection:
        for table in reversed(Base.metadata.sorted_tables):
            await connection.execute(table.delete())

    yield


@pytest_asyncio.fixture()
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    async with TestingSessionLocal() as session:
        yield session


@pytest_asyncio.fixture()
async def client(
    db_session: AsyncSession,
) -> AsyncGenerator[AsyncClient, None]:
    async def override_get_db() -> AsyncGenerator[AsyncSession, None]:
        yield db_session

    app.dependency_overrides[get_db] = override_get_db

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as test_client:
        yield test_client

    app.dependency_overrides.clear()


TEST_USER = {
    "email": "test@example.com",
    "password": "strongpassword",
}


@pytest_asyncio.fixture()
async def registered_user(client: AsyncClient) -> dict:
    response = await client.post(
        "/auth/register",
        json=TEST_USER,
    )
    assert response.status_code == 201, response.text
    return response.json()


@pytest_asyncio.fixture()
async def auth_headers(
    client: AsyncClient,
    registered_user: dict,
) -> dict[str, str]:
    response = await client.post(
        "/auth/login",
        data={
            "username": TEST_USER["email"],
            "password": TEST_USER["password"],
        },
    )
    assert response.status_code == 200, response.text

    return {
        "Authorization": f"Bearer {response.json()['access_token']}",
    }


@pytest_asyncio.fixture()
async def another_auth_headers(
    client: AsyncClient,
) -> dict[str, str]:
    email = "another@example.com"
    password = "strongpassword"

    register_response = await client.post(
        "/auth/register",
        json={
            "email": email,
            "password": password,
        },
    )
    assert register_response.status_code == 201, register_response.text

    login_response = await client.post(
        "/auth/login",
        data={
            "username": email,
            "password": password,
        },
    )
    assert login_response.status_code == 200, login_response.text

    return {
        "Authorization": (
            f"Bearer {login_response.json()['access_token']}"
        ),
    }


@pytest_asyncio.fixture()
async def project_id(
    client: AsyncClient,
    auth_headers: dict[str, str],
) -> int:
    response = await client.post(
        "/projects",
        headers=auth_headers,
        json={
            "name": "Test Project",
            "description": "Project for dataset tests",
        },
    )

    assert response.status_code == 201, response.text

    return int(response.json()["id"])


@pytest.fixture(autouse=True)
def override_upload_dir(tmp_path, monkeypatch) -> None:
    from app.api.routers import datasets as datasets_router

    upload_dir = tmp_path / "uploads" / "datasets"
    upload_dir.mkdir(parents=True, exist_ok=True)

    monkeypatch.setattr(
        datasets_router,
        "UPLOAD_DIR",
        upload_dir,
    )
