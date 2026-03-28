from __future__ import annotations

import os
import shutil
import subprocess
import sys
from pathlib import Path

import asyncpg
import pytest
from httpx import ASGITransport, AsyncClient
from testcontainers.postgres import PostgresContainer

from wallet_service.api.dependencies import get_wallet_service
from wallet_service.infrastructure.config import get_settings
from wallet_service.infrastructure.db.session import get_engine, get_session_factory
from wallet_service.main import create_app

PROJECT_ROOT = Path(__file__).resolve().parents[2]
POSTGRES_IMAGE = "postgres:16-alpine"


def _clear_runtime_caches() -> None:
    get_wallet_service.cache_clear()
    get_session_factory.cache_clear()
    get_engine.cache_clear()
    get_settings.cache_clear()


def _as_asyncpg_dsn(database_url: str) -> str:
    return database_url.replace("postgresql+asyncpg://", "postgresql://", 1)


@pytest.fixture(scope="session")
def postgres_container() -> PostgresContainer:
    if shutil.which("docker") is None:
        pytest.skip("Docker is required for PostgreSQL integration tests.")

    docker_info = subprocess.run(
        ["docker", "info"],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        check=False,
    )
    if docker_info.returncode != 0:
        pytest.skip("Docker daemon is not available for PostgreSQL integration tests.")

    with PostgresContainer(
        image=POSTGRES_IMAGE,
        username="postgres",
        password="postgres",
        dbname="wallet_service_test",
        driver="asyncpg",
    ) as postgres:
        yield postgres


@pytest.fixture(scope="session")
def postgres_database_url(postgres_container: PostgresContainer) -> str:
    return postgres_container.get_connection_url()


@pytest.fixture(scope="session")
def postgres_direct_url(postgres_container: PostgresContainer) -> str:
    return postgres_container.get_connection_url(driver=None)


@pytest.fixture(scope="session", autouse=True)
def configure_postgres_runtime(postgres_database_url: str) -> None:

    previous_database_url = os.environ.get("DATABASE_URL")
    migration_env = os.environ.copy()
    migration_env["DATABASE_URL"] = postgres_database_url

    _clear_runtime_caches()
    subprocess.run(
        [sys.executable, "-m", "alembic", "upgrade", "head"],
        cwd=PROJECT_ROOT,
        env=migration_env,
        check=True,
        text=True,
        capture_output=True,
    )

    os.environ["DATABASE_URL"] = postgres_database_url
    _clear_runtime_caches()

    try:
        yield
    finally:
        if previous_database_url is None:
            os.environ.pop("DATABASE_URL", None)
        else:
            os.environ["DATABASE_URL"] = previous_database_url
        _clear_runtime_caches()


@pytest.fixture
def app(postgres_database_url: str):
    _clear_runtime_caches()
    return create_app()


@pytest.fixture
async def client(app):
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://testserver",
    ) as async_client:
        yield async_client


@pytest.fixture(autouse=True)
async def reset_wallets(postgres_direct_url: str) -> None:
    connection = await asyncpg.connect(postgres_direct_url)
    try:
        await connection.execute("TRUNCATE TABLE wallets")
        yield
    finally:
        await connection.close()
        if get_engine.cache_info().currsize:
            await get_engine().dispose()
        _clear_runtime_caches()
