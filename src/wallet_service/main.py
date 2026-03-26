from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from wallet_service.api.routes import router as wallet_router
from wallet_service.domain.errors import InsufficientFundsError, WalletNotFoundError
from wallet_service.infrastructure.config import get_settings
from wallet_service.infrastructure.db.session import init_models


@asynccontextmanager
async def lifespan(_: FastAPI):
    settings = get_settings()
    if settings.auto_create_schema:
        await init_models()

    yield


def create_app() -> FastAPI:
    application = FastAPI(title="Wallet Service", version="0.1.0", lifespan=lifespan)
    application.include_router(wallet_router)

    @application.exception_handler(WalletNotFoundError)
    async def handle_wallet_not_found(
        request: Request,
        exc: WalletNotFoundError,
    ) -> JSONResponse:
        return JSONResponse(status_code=404, content={"detail": str(exc)})

    @application.exception_handler(InsufficientFundsError)
    async def handle_insufficient_funds(
        request: Request,
        exc: InsufficientFundsError,
    ) -> JSONResponse:
        return JSONResponse(status_code=409, content={"detail": str(exc)})

    return application


app = create_app()
