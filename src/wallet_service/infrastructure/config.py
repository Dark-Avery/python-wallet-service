from __future__ import annotations

import os
from dataclasses import dataclass, field
from functools import lru_cache


def _read_bool_env(name: str, default: bool) -> bool:
    raw_value = os.getenv(name)
    if raw_value is None:
        return default

    return raw_value.strip().lower() in {"1", "true"}


@dataclass(frozen=True, slots=True)
class Settings:
    database_url: str = field(
        default_factory=lambda: os.getenv("DATABASE_URL", "sqlite+aiosqlite:///./wallet.db")
    )
    auto_create_schema: bool = field(
        default_factory=lambda: _read_bool_env("AUTO_CREATE_SCHEMA", True)
    )


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
