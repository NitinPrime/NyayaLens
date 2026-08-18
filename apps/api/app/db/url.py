"""Database URL helpers for SQLite and Railway Postgres."""

from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

_ASYNC_DROP_KEYS = {"sslmode", "channel_binding", "sslrootcert"}


def normalize_database_url(url: str | None) -> str:
    """Railway provides postgresql://; SQLAlchemy async needs postgresql+asyncpg://."""
    if not url or not url.strip():
        return url or ""
    url = url.strip()
    if url.startswith("postgres://"):
        url = "postgresql://" + url[len("postgres://") :]
    if url.startswith("postgresql://") and "+asyncpg" not in url:
        url = "postgresql+asyncpg://" + url[len("postgresql://") :]
    if url.startswith("postgresql+asyncpg://"):
        url = _strip_libpq_query_params(url)
    return url


def normalize_sync_database_url(url: str | None) -> str:
    if not url or not url.strip():
        return url or ""
    url = url.strip()
    if url.startswith("postgres://"):
        url = "postgresql://" + url[len("postgres://") :]
    if "+asyncpg://" in url:
        url = url.replace("postgresql+asyncpg://", "postgresql://", 1)
    return url


def _strip_libpq_query_params(url: str) -> str:
    parts = urlsplit(url)
    kept = [(k, v) for k, v in parse_qsl(parts.query, keep_blank_values=True) if k.lower() not in _ASYNC_DROP_KEYS]
    return urlunsplit((parts.scheme, parts.netloc, parts.path, urlencode(kept), parts.fragment))


def postgres_connect_args(url: str) -> dict:
    """Private Railway Postgres has no TLS; public proxy URLs often require it."""
    lower = url.lower()
    if "railway.internal" in lower:
        return {}
    if "sslmode=require" in lower or "rlwy.net" in lower:
        return {"ssl": True}
    return {}
