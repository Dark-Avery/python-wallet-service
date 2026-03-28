from __future__ import annotations

import asyncio
from uuid import UUID, uuid4

import asyncpg
import pytest
from httpx import ASGITransport, AsyncClient, Response
from starlette.status import HTTP_200_OK, HTTP_409_CONFLICT

from wallet_service.main import create_app


async def _insert_wallet(database_url: str, wallet_uuid: UUID, balance: int) -> None:
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


async def _post_operation(
    wallet_uuid: UUID,
    operation_type: str,
    amount: int,
) -> tuple[str, Response]:
    app = create_app()
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://testserver",
    ) as client:
        response = await client.post(
            f"/api/v1/wallets/{wallet_uuid}/operation",
            json={"operation_type": operation_type, "amount": amount},
        )
        return operation_type, response


@pytest.mark.asyncio
@pytest.mark.integration
async def test_concurrent_deposits_to_new_wallet_preserve_total_balance(
    postgres_direct_url: str,
) -> None:
    wallet_uuid = uuid4()
    deposit_count = 10
    deposit_amount = 25

    responses = await asyncio.gather(
        *[
            _post_operation(wallet_uuid, "DEPOSIT", deposit_amount)
            for _ in range(deposit_count)
        ]
    )

    assert all(response.status_code == HTTP_200_OK for _, response in responses)
    assert await _fetch_balance(postgres_direct_url, wallet_uuid) == (
        deposit_count * deposit_amount
    )


@pytest.mark.asyncio
@pytest.mark.integration
async def test_concurrent_withdrawals_never_overdraw_wallet(
    postgres_direct_url: str,
) -> None:
    wallet_uuid = uuid4()
    initial_balance = 100
    withdraw_count = 10
    withdraw_amount = 15
    await _insert_wallet(postgres_direct_url, wallet_uuid, initial_balance)

    responses = await asyncio.gather(
        *[
            _post_operation(wallet_uuid, "WITHDRAW", withdraw_amount)
            for _ in range(withdraw_count)
        ]
    )

    success_count = sum(response.status_code == HTTP_200_OK for _, response in responses)
    conflict_count = sum(
        response.status_code == HTTP_409_CONFLICT for _, response in responses
    )

    assert success_count == initial_balance // withdraw_amount
    assert conflict_count == withdraw_count - success_count
    assert await _fetch_balance(postgres_direct_url, wallet_uuid) == (
        initial_balance - success_count * withdraw_amount
    )


@pytest.mark.asyncio
@pytest.mark.integration
async def test_mixed_concurrent_operations_keep_balance_consistent(
    postgres_direct_url: str,
) -> None:
    wallet_uuid = uuid4()
    initial_balance = 100
    deposit_amount = 20
    withdraw_amount = 15
    await _insert_wallet(postgres_direct_url, wallet_uuid, initial_balance)

    responses = await asyncio.gather(
        *[_post_operation(wallet_uuid, "DEPOSIT", deposit_amount) for _ in range(5)],
        *[_post_operation(wallet_uuid, "WITHDRAW", withdraw_amount) for _ in range(8)],
    )

    success_deposits = sum(
        operation_type == "DEPOSIT" and response.status_code == HTTP_200_OK
        for operation_type, response in responses
    )
    success_withdrawals = sum(
        operation_type == "WITHDRAW" and response.status_code == HTTP_200_OK
        for operation_type, response in responses
    )

    final_balance = await _fetch_balance(postgres_direct_url, wallet_uuid)

    assert final_balance is not None
    assert final_balance >= 0
    assert final_balance == (
        initial_balance
        + success_deposits * deposit_amount
        - success_withdrawals * withdraw_amount
    )
