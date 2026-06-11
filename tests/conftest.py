"""Shared test fixtures.

v0.6.0: pytest session auto-isolates tests from production DB.

Strategy: monkeypatch `chronocare.database.engine` and `async_session_factory`
to point at a tmp DB (copy of prod via SQLite .backup). The database.py module
itself is unchanged.

Why monkeypatch (vs env-override on database.py):
- database.py stays untouched (smaller, more reviewable diff)
- pytest-native pattern, automatic teardown via monkeypatch
- concurrent-safe (pytest-xdist gets fresh tmp per worker)
- backwards-compatible: production uvicorn on :8000 still uses original engine

Why autouse=True + scope="session": one swap per pytest run, all tests benefit.
"""

import os
import sqlite3
from pathlib import Path

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import NullPool

from chronocare.config import settings


def _resolve_prod_db_path() -> Path:
    """Resolve prod DB path from settings.database_url.

    settings.base_dir is buggy (off by one parent in this repo). Use database_url
    resolved against cwd instead — same logic the live engine uses.
    """
    url = settings.database_url
    # sqlite+aiosqlite:///./data/foo.db -> ./data/foo.db (relative to cwd)
    prefix = "sqlite+aiosqlite:///"
    if not url.startswith(prefix):
        raise RuntimeError(f"unexpected database_url scheme: {url}")
    rel = url[len(prefix):]
    return Path(os.path.abspath(rel))


@pytest.fixture(scope="session", autouse=True)
def _isolated_engine(tmp_path_factory):
    """Copy prod DB to tmp, swap chronocare.database.engine + factory.

    session-scoped: one tmp DB per pytest run.
    autouse=True: every test gets isolated DB.
    teardown: pytest.MonkeyPatch instance auto-restores on session end.
    """
    import chronocare.database as db

    # Build tmp DB path
    tmp_dir = tmp_path_factory.mktemp("chronocare-test")
    test_db = tmp_dir / "chronocare-test.db"

    # Resolve prod DB path from settings.database_url (NOT settings.base_dir).
    prod_db = _resolve_prod_db_path()
    if prod_db.exists():
        src_conn = sqlite3.connect(str(prod_db))
        dst_conn = sqlite3.connect(str(test_db))
        try:
            src_conn.backup(dst_conn)
            dst_conn.commit()
        finally:
            dst_conn.close()
            src_conn.close()
    else:
        # Fresh CI checkout - no prod to copy. Touch empty file so SQLite can create schema.
        test_db.touch()

    # Build test engine pointing at tmp DB
    test_engine = create_async_engine(
        f"sqlite+aiosqlite:///{test_db}",
        echo=False,
        poolclass=NullPool,
    )
    test_factory = async_sessionmaker(
        test_engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )

    # Manually manage monkeypatch (pytest builtin monkeypatch is function-scoped;
    # we need session-scoped teardown for the engine swap).
    mp = pytest.MonkeyPatch()
    mp.setattr(db, "engine", test_engine)
    mp.setattr(db, "async_session_factory", test_factory)

    yield  # tests run with isolated engine

    # Teardown: restore original engine + factory on db module
    mp.undo()
    # tmp_path_factory auto-cleans the tmp dir


@pytest.fixture
async def client():
    """Async test client for FastAPI."""
    from chronocare.main import app

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        yield ac
