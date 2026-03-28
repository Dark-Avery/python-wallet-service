from __future__ import annotations

from uuid import UUID

from sqlalchemy import BigInteger, CheckConstraint, Uuid
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class WalletModel(Base):
    __tablename__ = "wallets"
    __table_args__ = (CheckConstraint(
        "balance >= 0", name="ck_wallets_balance_non_negative"),)

    wallet_uuid: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True), primary_key=True)
    balance: Mapped[int] = mapped_column(BigInteger, nullable=False, default=0)
