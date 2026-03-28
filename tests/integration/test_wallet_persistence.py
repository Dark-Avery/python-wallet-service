from __future__ import annotations

from uuid import UUID, uuid4

import asyncpg
import pytest
from httpx import AsyncClient


async def _insert_wallet(
    database_url: str,
    wallet_uuid: UUID,
    balance: int,
) -> None:
    connection = await asyncpg.connect(database_url)
    try:
        await connection.execute(
            "INSERT INTO wallets (wallet_uuid, balance) VALUES ($1, $2)",
            wallet_uuid,
            balance,
        )
    finally:
        await connection.close()


async def _fetch_balance(database_url: str, wallet_uuid: UUID) -> int | None:
    connection = await asyncpg.connect(database_url)
    try:
        return await connection.fetchval(
            "SELECT balance FROM wallets WHERE wallet_uuid = $1",
            wallet_uuid,
        )
    finally:
        await connection.close()


@pytest.mark.asyncio
@pytest.mark.integration
async def test_deposit_persists_wallet_balance(
    client: AsyncClient,
    postgres_direct_url: str,
) -> None:
    wallet_uuid = uuid4()

    response = await client.post(
        f"/api/v1/wallets/{wallet_uuid}/operation",
        json={"operation_type": "DEPOSIT", "amount": 125},
    )

    assert response.status_code == 200
    assert response.json() == {"wallet_uuid": str(wallet_uuid), "balance": 125}
    assert await _fetch_balance(postgres_direct_url, wallet_uuid) == 125


@pytest.mark.asyncio
@pytest.mark.integration
async def test_get_wallet_reads_persisted_balance(
    client: AsyncClient,
    postgres_direct_url: str,
) -> None:
    wallet_uuid = uuid4()
    await _insert_wallet(postgres_direct_url, wallet_uuid, 310)

    response = await client.get(f"/api/v1/wallets/{wallet_uuid}")

    assert response.status_code == 200
    assert response.json() == {"wallet_uuid": str(wallet_uuid), "balance": 310}


@pytest.mark.asyncio
@pytest.mark.integration
async def test_withdraw_updates_persisted_balance(
    client: AsyncClient,
    postgres_direct_url: str,
) -> None:
    wallet_uuid = uuid4()
    await _insert_wallet(postgres_direct_url, wallet_uuid, 200)

    response = await client.post(
        f"/api/v1/wallets/{wallet_uuid}/operation",
        json={"operation_type": "WITHDRAW", "amount": 75},
    )

    assert response.status_code == 200
    assert response.json() == {"wallet_uuid": str(wallet_uuid), "balance": 125}
    assert await _fetch_balance(postgres_direct_url, wallet_uuid) == 125


@pytest.mark.asyncio
@pytest.mark.integration
async def test_withdraw_insufficient_funds_keeps_persisted_balance(
    client: AsyncClient,
    postgres_direct_url: str,
) -> None:
    wallet_uuid = uuid4()
    await _insert_wallet(postgres_direct_url, wallet_uuid, 30)

    response = await client.post(
        f"/api/v1/wallets/{wallet_uuid}/operation",
        json={"operation_type": "WITHDRAW", "amount": 50},
    )

    assert response.status_code == 409
    assert await _fetch_balance(postgres_direct_url, wallet_uuid) == 30
