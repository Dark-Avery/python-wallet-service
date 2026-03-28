from __future__ import annotations

from uuid import UUID

from wallet_service.application.contracts import WalletRepositoryFactory
from wallet_service.domain.entities import OperationType, Wallet
from wallet_service.domain.errors import (
    InsufficientFundsError,
    WalletNotFoundError,
)


class WalletService:
    def __init__(self, repository_factory: WalletRepositoryFactory) -> None:
        self._repository_factory = repository_factory

    async def get_wallet(self, wallet_uuid: UUID) -> Wallet:
        async with self._repository_factory() as repository:
            wallet = await repository.get(wallet_uuid)

        if wallet is None:
            raise WalletNotFoundError(f"Wallet {wallet_uuid} was not found.")

        return wallet

    async def apply_operation(
        self,
        wallet_uuid: UUID,
        operation_type: OperationType,
        amount: int,
    ) -> Wallet:
        if amount <= 0:
            raise ValueError("Amount must be positive.")

        async with self._repository_factory() as repository:
            if operation_type is OperationType.DEPOSIT:
                updated_wallet = await repository.deposit(wallet_uuid, amount=amount)
                await repository.commit()
                return updated_wallet

            wallet = await repository.get(wallet_uuid, for_update=True)

            if wallet is None:
                raise WalletNotFoundError(f"Wallet {wallet_uuid} was not found.")

            if wallet.balance < amount:
                raise InsufficientFundsError(
                    f"Wallet {wallet_uuid} does not have enough funds."
                )

            updated_wallet = await repository.update_balance(
                wallet_uuid,
                balance=wallet.balance - amount,
            )
            await repository.commit()
            return updated_wallet
