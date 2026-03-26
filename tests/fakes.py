from __future__ import annotations

from copy import deepcopy
from types import TracebackType
from uuid import UUID

from wallet_service.domain.entities import Wallet


class FakeWalletRepository:
    def __init__(self, store: dict[UUID, int] | None = None) -> None:
        self._store = store if store is not None else {}
        self._snapshot: dict[UUID, int] = {}

    async def __aenter__(self) -> "FakeWalletRepository":
        self._snapshot = deepcopy(self._store)
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        tb: TracebackType | None,
    ) -> None:
        if exc is not None:
            self._store.clear()
            self._store.update(self._snapshot)

    async def get(self, wallet_uuid: UUID, *, for_update: bool = False) -> Wallet | None:
        balance = self._store.get(wallet_uuid)
        if balance is None:
            return None

        return Wallet(wallet_uuid=wallet_uuid, balance=balance)

    async def create(self, wallet_uuid: UUID, *, balance: int) -> Wallet:
        self._store[wallet_uuid] = balance
        return Wallet(wallet_uuid=wallet_uuid, balance=balance)

    async def update_balance(self, wallet_uuid: UUID, *, balance: int) -> Wallet:
        self._store[wallet_uuid] = balance
        return Wallet(wallet_uuid=wallet_uuid, balance=balance)

    async def commit(self) -> None:
        return None
