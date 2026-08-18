from app.config import normalize_database_url, normalize_sync_database_url


def test_railway_postgres_url_becomes_asyncpg():
    raw = "postgresql://postgres:pass@postgres.railway.internal:5432/railway"
    assert normalize_database_url(raw) == (
        "postgresql+asyncpg://postgres:pass@postgres.railway.internal:5432/railway"
    )


def test_postgres_scheme_is_normalized():
    raw = "postgres://user:pass@host:5432/db"
    assert normalize_database_url(raw).startswith("postgresql+asyncpg://")


def test_sqlite_unchanged():
    raw = "sqlite+aiosqlite:///./data/nyayalens.db"
    assert normalize_database_url(raw) == raw


def test_sync_url_strips_asyncpg():
    raw = "postgresql+asyncpg://user:pass@host:5432/db"
    assert normalize_sync_database_url(raw) == "postgresql://user:pass@host:5432/db"
