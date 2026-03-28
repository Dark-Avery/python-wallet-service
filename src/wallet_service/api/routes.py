from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, status

from wallet_service.api.dependencies import get_wallet_service
from wallet_service.api.schemas import WalletOperationRequest, WalletResponse
from wallet_service.application.services import WalletService

router = APIRouter(prefix="/api/v1/wallets", tags=["wallets"])


@router.post(
    "/{wallet_uuid}/operation",
    response_model=WalletResponse,
    status_code=status.HTTP_200_OK,
)
async def apply_wallet_operation(
    wallet_uuid: UUID,
    request: WalletOperationRequest,
    service: WalletService = Depends(get_wallet_service),
) -> WalletResponse:
    wallet = await service.apply_operation(
        wallet_uuid=wallet_uuid,
        operation_type=request.operation_type,
        amount=request.amount,
    )
    return WalletResponse.model_validate(wallet)


@router.get(
    "/{wallet_uuid}",
    response_model=WalletResponse,
    status_code=status.HTTP_200_OK,
)
async def get_wallet(
    wallet_uuid: UUID,
    service: WalletService = Depends(get_wallet_service),
) -> WalletResponse:
    wallet = await service.get_wallet(wallet_uuid)
    return WalletResponse.model_validate(wallet)
