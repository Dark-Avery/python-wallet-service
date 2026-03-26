from __future__ import annotations

from functools import lru_cache

from wallet_service.application.contracts import WalletRepository
from wallet_service.application.services import WalletService
from wallet_service.infrastructure.db.repositories import SQLAlchemyWalletRepository
from wallet_service.infrastructure.db.session import get_session_factory


def build_wallet_repository() -> WalletRepository:
    return SQLAlchemyWalletRepository(get_session_factory())


@lru_cache(maxsize=1)
def get_wallet_service() -> WalletService:
    return WalletService(repository_factory=build_wallet_repository)
