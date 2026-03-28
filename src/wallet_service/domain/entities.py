from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from uuid import UUID


class OperationType(StrEnum):
    DEPOSIT = "DEPOSIT"
    WITHDRAW = "WITHDRAW"


@dataclass(slots=True)
class Wallet:
    wallet_uuid: UUID
    balance: int
