"""Application configuration."""

from functools import lru_cache
from pathlib import Path
from typing import List

from pydantic_settings import BaseSettings, SettingsConfigDict

# Repo root: apps/api/app/config.py -> ../../../
REPO_ROOT = Path(__file__).resolve().parents[3]
DATA_DIR = REPO_ROOT / "data"
DEFAULT_SQLITE_PATH = DATA_DIR / "nyayalens.db"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=str(REPO_ROOT / ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # Database — SQLite default for local dev without Docker
    database_url: str = f"sqlite+aiosqlite:///{DEFAULT_SQLITE_PATH.as_posix()}"
    database_url_sync: str = f"sqlite:///{DEFAULT_SQLITE_PATH.as_posix()}"

    # API
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    api_secret_key: str = "change-me-in-production"
    cors_origins: str = "http://localhost:3000"

    # LLM
    llm_provider: str = "mock"
    openai_api_key: str = ""
    anthropic_api_key: str = ""
    llm_model: str = "gpt-4o-mini"

    # Embeddings
    embedding_provider: str = "mock"
    embedding_model: str = "text-embedding-3-small"
    embedding_dimension: int = 1536

    # Auth
    jwt_secret_key: str = "change-me-jwt-secret"
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 1440

    # Logging
    log_level: str = "INFO"

    # Uploads
    max_upload_size_mb: int = 25
    upload_dir: str = str(REPO_ROOT / "uploads")

    @property
    def cors_origins_list(self) -> List[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]

    @property
    def is_sqlite(self) -> bool:
        return self.database_url.startswith("sqlite")


@lru_cache
def get_settings() -> Settings:
    settings = Settings()
    if settings.is_sqlite and settings.database_url.startswith("sqlite+aiosqlite:///./"):
        db_path = REPO_ROOT / settings.database_url.replace("sqlite+aiosqlite:///./", "")
        db_path.parent.mkdir(parents=True, exist_ok=True)
        settings.database_url = f"sqlite+aiosqlite:///{db_path.as_posix()}"
        settings.database_url_sync = f"sqlite:///{db_path.as_posix()}"
    return settings
