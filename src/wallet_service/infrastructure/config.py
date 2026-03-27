from __future__ import annotations

import os
from dataclasses import dataclass, field
from functools import lru_cache


@dataclass(frozen=True, slots=True)
class Settings:
    database_url: str = field(
        default_factory=lambda: os.getenv("DATABASE_URL", "sqlite+aiosqlite:///./wallet.db")
    )


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
