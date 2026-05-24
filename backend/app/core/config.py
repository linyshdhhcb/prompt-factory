from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Optional

import yaml
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


_CONFIG_DIR = Path(__file__).resolve().parent.parent.parent


def _load_yaml_config() -> dict:
    config_path = _CONFIG_DIR / "config.yaml"
    if config_path.exists():
        with open(config_path, "r", encoding="utf-8") as f:
            return yaml.safe_load(f) or {}
    return {}


def _flatten_yaml(data: dict, prefix: str = "") -> dict[str, object]:
    out: dict[str, object] = {}
    for key, value in data.items():
        full_key = f"{prefix}{key}" if not prefix else f"{prefix}_{key}"
        if isinstance(value, dict):
            out.update(_flatten_yaml(value, full_key))
        else:
            out[full_key.upper()] = value
    return out


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )

    DATABASE_URL: str = "postgresql+asyncpg://pf_user:password@localhost:5432/prompt_factory"

    SECRET_KEY: str = "change-me-in-production-use-a-random-string"

    DB_POOL_SIZE: int = 10
    DB_MAX_OVERFLOW: int = 20

    EMBEDDING_PROVIDER: str = "openai"
    EMBEDDING_MODEL: str = "text-embedding-3-small"
    EMBEDDING_API_KEY_ENV: str = "OPENAI_KEY"
    EMBEDDING_BASE_URL: str = "https://api.openai.com/v1"
    EMBEDDING_DIMENSION: int = 1536

    GENERATION_CONCURRENCY: int = 5
    LLM_TIMEOUT_SECONDS: int = 30
    EMBEDDING_TIMEOUT_SECONDS: int = 15

    SIMILARITY_THRESHOLD: float = 0.85
    HUMAN_LIKENESS: str = "medium"

    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"

    @classmethod
    def load(cls) -> Settings:
        yaml_data = _load_yaml_config()
        flat_env = _flatten_yaml(yaml_data)
        env_overrides = {}
        for key, value in flat_env.items():
            if key in cls.model_fields:
                env_overrides[key] = value
        return cls(**env_overrides)


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings.load()
