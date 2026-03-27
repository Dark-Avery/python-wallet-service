from __future__ import annotations

import os
from dataclasses import dataclass, field
from functools import lru_cache
from urllib.parse import quote_plus


@dataclass(frozen=True, slots=True)
class Settings:
    database_url: str | None = field(default_factory=lambda: os.getenv("DATABASE_URL"))
    db_driver: str = field(
        default_factory=lambda: os.getenv("DB_DRIVER", "postgresql+asyncpg")
    )
    db_host: str = field(default_factory=lambda: os.getenv("DB_HOST", "localhost"))
    db_port: int = field(default_factory=lambda: int(os.getenv("DB_PORT", "5432")))
    db_name: str = field(default_factory=lambda: os.getenv("DB_NAME", "wallet_service"))
    db_user: str = field(default_factory=lambda: os.getenv("DB_USER", "postgres"))
    db_password: str = field(default_factory=lambda: os.getenv("DB_PASSWORD", "postgres"))

    @property
    def sqlalchemy_database_url(self) -> str:
        if self.database_url:
            return self.database_url

        encoded_password = quote_plus(self.db_password)
        return (
            f"{self.db_driver}://{self.db_user}:{encoded_password}"
            f"@{self.db_host}:{self.db_port}/{self.db_name}"
        )


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
