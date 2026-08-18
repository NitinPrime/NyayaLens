from app.db.url import normalize_database_url as normalize
from app.db.url import postgres_connect_args


def test_railway_postgres_url_becomes_asyncpg():
    raw = "postgresql://postgres:pass@postgres.railway.internal:5432/railway"
    assert normalize(raw) == (
        "postgresql+asyncpg://postgres:pass@postgres.railway.internal:5432/railway"
    )


def test_strips_sslmode_for_asyncpg():
    raw = "postgresql://postgres:pass@host:5432/railway?sslmode=require"
    assert "sslmode" not in normalize(raw)
    assert normalize(raw).startswith("postgresql+asyncpg://")


def test_internal_railway_does_not_force_ssl():
    url = "postgresql+asyncpg://postgres:pass@postgres.railway.internal:5432/railway"
    assert postgres_connect_args(url) == {}


def test_public_proxy_uses_ssl():
    url = "postgresql+asyncpg://postgres:pass@switchyard.proxy.rlwy.net:1234/railway"
    assert postgres_connect_args(url) == {"ssl": True}


def test_sqlite_unchanged():
    raw = "sqlite+aiosqlite:///./data/nyayalens.db"
    assert normalize(raw) == raw
