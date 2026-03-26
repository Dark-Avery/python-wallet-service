from __future__ import annotations

from uuid import uuid4

import pytest

from tests.fakes import FakeWalletRepository
from wallet_service.application.services import WalletService
from wallet_service.domain.entities import OperationType
from wallet_service.domain.errors import (
    InsufficientFundsError,
    WalletNotFoundError,
)


def build_service(store: dict | None = None) -> tuple[WalletService, dict]:
    repository_store: dict = {} if store is None else store

    def repository_factory() -> FakeWalletRepository:
        return FakeWalletRepository(repository_store)

    return WalletService(repository_factory=repository_factory), repository_store


@pytest.mark.asyncio
async def test_deposit_creates_new_wallet() -> None:
    service, store = build_service()
    wallet_uuid = uuid4()

    wallet = await service.apply_operation(wallet_uuid, OperationType.DEPOSIT, 100)

    assert wallet.balance == 100
    assert store[wallet_uuid] == 100


@pytest.mark.asyncio
async def test_deposit_updates_existing_wallet() -> None:
    wallet_uuid = uuid4()
    service, store = build_service({wallet_uuid: 150})

    wallet = await service.apply_operation(wallet_uuid, OperationType.DEPOSIT, 50)

    assert wallet.balance == 200
    assert store[wallet_uuid] == 200


@pytest.mark.asyncio
async def test_withdraw_reduces_balance() -> None:
    wallet_uuid = uuid4()
    service, store = build_service({wallet_uuid: 150})

    wallet = await service.apply_operation(wallet_uuid, OperationType.WITHDRAW, 40)

    assert wallet.balance == 110
    assert store[wallet_uuid] == 110


@pytest.mark.asyncio
async def test_withdraw_raises_for_insufficient_funds() -> None:
    wallet_uuid = uuid4()
    service, store = build_service({wallet_uuid: 10})

    with pytest.raises(InsufficientFundsError):
        await service.apply_operation(wallet_uuid, OperationType.WITHDRAW, 20)

    assert store[wallet_uuid] == 10


@pytest.mark.asyncio
async def test_withdraw_raises_for_missing_wallet() -> None:
    service, _ = build_service()

    with pytest.raises(WalletNotFoundError):
        await service.apply_operation(uuid4(), OperationType.WITHDRAW, 20)


@pytest.mark.asyncio
async def test_get_wallet_returns_existing_wallet() -> None:
    wallet_uuid = uuid4()
    service, _ = build_service({wallet_uuid: 55})

    wallet = await service.get_wallet(wallet_uuid)

    assert wallet.wallet_uuid == wallet_uuid
    assert wallet.balance == 55


@pytest.mark.asyncio
async def test_get_wallet_raises_for_missing_wallet() -> None:
    service, _ = build_service()

    with pytest.raises(WalletNotFoundError):
        await service.get_wallet(uuid4())


@pytest.mark.asyncio
@pytest.mark.parametrize("amount", [0, -1])
async def test_apply_operation_rejects_non_positive_amount(amount: int) -> None:
    service, _ = build_service()

    with pytest.raises(ValueError):
        await service.apply_operation(uuid4(), OperationType.DEPOSIT, amount)
