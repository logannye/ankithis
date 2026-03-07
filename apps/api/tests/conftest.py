import asyncio

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import create_async_engine

from ankithis_api.app import app
from ankithis_api.config import settings
from ankithis_api.models.base import Base
import ankithis_api.models  # noqa: F401  — register all models in metadata


@pytest.fixture(scope="session")
def event_loop():
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session", autouse=True)
def setup_database(event_loop):
    """Create all tables before tests, drop after."""
    engine = create_async_engine(settings.database_url, echo=False)

    async def _setup():
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)
            await conn.run_sync(Base.metadata.create_all)

    async def _teardown():
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)
        await engine.dispose()

    event_loop.run_until_complete(_setup())
    yield
    event_loop.run_until_complete(_teardown())


@pytest.fixture
def client(setup_database):
    return TestClient(app)
