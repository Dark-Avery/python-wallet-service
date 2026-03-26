from __future__ import annotations

from types import TracebackType
from uuid import UUID

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from wallet_service.domain.entities import Wallet
from wallet_service.infrastructure.db.models import WalletModel


class SQLAlchemyWalletRepository:
    def __init__(self, session_factory: async_sessionmaker[AsyncSession]) -> None:
        self._session_factory = session_factory
        self._session: AsyncSession | None = None

    async def __aenter__(self) -> "SQLAlchemyWalletRepository":
        self._session = self._session_factory()
        await self._session.begin()
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        tb: TracebackType | None,
    ) -> None:
        if self._session is None:
            return

        try:
            if exc is not None and self._session.in_transaction():
                await self._session.rollback()
        finally:
            await self._session.close()
            self._session = None

    async def get(self, wallet_uuid: UUID, *, for_update: bool = False) -> Wallet | None:
        session = self._require_session()
        statement = select(WalletModel).where(WalletModel.wallet_uuid == wallet_uuid)
        if for_update:
            statement = statement.with_for_update()

        result = await session.execute(statement)
        wallet = result.scalar_one_or_none()
        if wallet is None:
            return None

        return Wallet(wallet_uuid=wallet.wallet_uuid, balance=wallet.balance)

    async def create(self, wallet_uuid: UUID, *, balance: int) -> Wallet:
        session = self._require_session()
        wallet = WalletModel(wallet_uuid=wallet_uuid, balance=balance)
        session.add(wallet)
        await session.flush()
        return Wallet(wallet_uuid=wallet.wallet_uuid, balance=wallet.balance)

    async def update_balance(self, wallet_uuid: UUID, *, balance: int) -> Wallet:
        session = self._require_session()
        statement = (
            update(WalletModel)
            .where(WalletModel.wallet_uuid == wallet_uuid)
            .values(balance=balance)
            .returning(WalletModel.wallet_uuid, WalletModel.balance)
        )
        result = await session.execute(statement)
        updated_wallet = result.one()
        return Wallet(wallet_uuid=updated_wallet.wallet_uuid, balance=updated_wallet.balance)

    async def commit(self) -> None:
        session = self._require_session()
        await session.commit()

    def _require_session(self) -> AsyncSession:
        if self._session is None:
            raise RuntimeError("Repository session is not initialized.")

        return self._session
