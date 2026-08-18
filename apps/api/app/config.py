"""Application configuration."""

from functools import lru_cache
from pathlib import Path
from typing import List, Optional

from pydantic_settings import BaseSettings, SettingsConfigDict

from app.db.url import normalize_database_url, normalize_sync_database_url

_HERE = Path(__file__).resolve()
REPO_ROOT = _HERE.parents[3] if (_HERE.parents[3] / "data" / "legal_sources").exists() else _HERE.parents[1]
DATA_DIR = REPO_ROOT / "data"
DEFAULT_SQLITE_PATH = DATA_DIR / "nyayalens.db"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=str(REPO_ROOT / ".env") if (REPO_ROOT / ".env").exists() else None,
        env_file_encoding="utf-8",
        extra="ignore",
    )

    database_url: str = f"sqlite+aiosqlite:///{DEFAULT_SQLITE_PATH.as_posix()}"
    database_url_sync: str = f"sqlite:///{DEFAULT_SQLITE_PATH.as_posix()}"

    api_host: str = "0.0.0.0"
    api_port: int = 8000
    api_secret_key: str = "change-me-in-production"
    cors_origins: str = "*"

    llm_provider: str = "mock"
    openai_api_key: str = ""
    anthropic_api_key: str = ""
    llm_model: str = "gpt-4o-mini"

    embedding_provider: str = "mock"
    embedding_model: str = "text-embedding-3-small"
    embedding_dimension: int = 1536

    jwt_secret_key: str = "change-me-jwt-secret"
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 1440

    log_level: str = "INFO"

    max_upload_size_mb: int = 25
    upload_dir: str = str(REPO_ROOT / "uploads")

    @property
    def cors_origins_list(self) -> List[str]:
        origins = [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]
        return origins or ["*"]

    @property
    def is_sqlite(self) -> bool:
        return self.database_url.startswith("sqlite")


@lru_cache
def get_settings() -> Settings:
    settings = Settings()
    raw = (settings.database_url or "").strip()
    if not raw:
        raw = f"sqlite+aiosqlite:///{DEFAULT_SQLITE_PATH.as_posix()}"
    settings.database_url = normalize_database_url(raw)
    settings.database_url_sync = normalize_sync_database_url(settings.database_url_sync or settings.database_url)
    if settings.is_sqlite:
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        Path(settings.upload_dir).mkdir(parents=True, exist_ok=True)
    return settings
