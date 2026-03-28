from __future__ import annotations

from collections.abc import Callable
from typing import Protocol, Self
from uuid import UUID

from wallet_service.domain.entities import Wallet


class WalletRepository(Protocol):
    async def __aenter__(self) -> Self:
        ...

    async def __aexit__(self, exc_type, exc, tb) -> None:
        ...

    async def get(
        self,
        wallet_uuid: UUID,
        *,
        for_update: bool = False,
    ) -> Wallet | None:
        ...

    async def deposit(self, wallet_uuid: UUID, *, amount: int) -> Wallet:
        ...

    async def update_balance(
        self,
        wallet_uuid: UUID,
        *,
        balance: int,
    ) -> Wallet:
        ...

    async def commit(self) -> None:
        ...


WalletRepositoryFactory = Callable[[], WalletRepository]
