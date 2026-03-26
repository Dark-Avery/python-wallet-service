from __future__ import annotations

from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from wallet_service.domain.entities import OperationType


class WalletOperationRequest(BaseModel):
    operation_type: OperationType
    amount: int = Field(gt=0)


class WalletResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    wallet_uuid: UUID
    balance: int
