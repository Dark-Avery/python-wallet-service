from __future__ import annotations

from uuid import UUID, uuid4

import pytest
from httpx import ASGITransport, AsyncClient

from tests.fakes import FakeWalletRepository
from wallet_service.api.dependencies import get_wallet_service
from wallet_service.application.services import WalletService
from wallet_service.infrastructure.config import get_settings
from wallet_service.main import create_app


@pytest.fixture
def store() -> dict[UUID, int]:
    return {}


@pytest.fixture
def app(monkeypatch: pytest.MonkeyPatch, store: dict[UUID, int]):
    monkeypatch.setenv("AUTO_CREATE_SCHEMA", "0")
    get_settings.cache_clear()

    def repository_factory() -> FakeWalletRepository:
        return FakeWalletRepository(store)

    application = create_app()
    application.dependency_overrides[get_wallet_service] = lambda: WalletService(
        repository_factory=repository_factory
    )
    return application


@pytest.fixture
async def client(app):
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://testserver",
    ) as async_client:
        yield async_client


@pytest.mark.asyncio
async def test_post_operation_returns_updated_wallet(client: AsyncClient, store: dict[UUID, int]) -> None:
    wallet_uuid = uuid4()

    response = await client.post(
        f"/api/v1/wallets/{wallet_uuid}/operation",
        json={"operation_type": "DEPOSIT", "amount": 125},
    )

    assert response.status_code == 200
    assert response.json() == {"wallet_uuid": str(wallet_uuid), "balance": 125}
    assert store[wallet_uuid] == 125


@pytest.mark.asyncio
async def test_get_wallet_returns_balance(client: AsyncClient, store: dict[UUID, int]) -> None:
    wallet_uuid = uuid4()
    store[wallet_uuid] = 310

    response = await client.get(f"/api/v1/wallets/{wallet_uuid}")

    assert response.status_code == 200
    assert response.json() == {"wallet_uuid": str(wallet_uuid), "balance": 310}


@pytest.mark.asyncio
async def test_get_missing_wallet_returns_404(client: AsyncClient) -> None:
    response = await client.get(f"/api/v1/wallets/{uuid4()}")

    assert response.status_code == 404


@pytest.mark.asyncio
async def test_withdraw_returns_updated_wallet(client: AsyncClient, store: dict[UUID, int]) -> None:
    wallet_uuid = uuid4()
    store[wallet_uuid] = 200

    response = await client.post(
        f"/api/v1/wallets/{wallet_uuid}/operation",
        json={"operation_type": "WITHDRAW", "amount": 75},
    )

    assert response.status_code == 200
    assert response.json() == {"wallet_uuid": str(wallet_uuid), "balance": 125}
    assert store[wallet_uuid] == 125


@pytest.mark.asyncio
async def test_withdraw_missing_wallet_returns_404(client: AsyncClient) -> None:
    response = await client.post(
        f"/api/v1/wallets/{uuid4()}/operation",
        json={"operation_type": "WITHDRAW", "amount": 100},
    )

    assert response.status_code == 404


@pytest.mark.asyncio
async def test_withdraw_with_insufficient_funds_returns_409(
    client: AsyncClient,
    store: dict[UUID, int],
) -> None:
    wallet_uuid = uuid4()
    store[wallet_uuid] = 30

    response = await client.post(
        f"/api/v1/wallets/{wallet_uuid}/operation",
        json={"operation_type": "WITHDRAW", "amount": 50},
    )

    assert response.status_code == 409
    assert store[wallet_uuid] == 30


@pytest.mark.asyncio
async def test_post_operation_rejects_invalid_operation_type(client: AsyncClient) -> None:
    response = await client.post(
        f"/api/v1/wallets/{uuid4()}/operation",
        json={"operation_type": "TRANSFER", "amount": 100},
    )

    assert response.status_code == 422


@pytest.mark.asyncio
@pytest.mark.parametrize("amount", [0, -10])
async def test_post_operation_rejects_non_positive_amount(
    client: AsyncClient,
    amount: int,
) -> None:
    response = await client.post(
        f"/api/v1/wallets/{uuid4()}/operation",
        json={"operation_type": "DEPOSIT", "amount": amount},
    )

    assert response.status_code == 422


@pytest.mark.asyncio
async def test_invalid_wallet_uuid_returns_422(client: AsyncClient) -> None:
    response = await client.get("/api/v1/wallets/not-a-uuid")

    assert response.status_code == 422
