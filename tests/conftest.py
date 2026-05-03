"""Shared test fixtures."""

import pytest
from httpx import ASGITransport, AsyncClient

from chronocare.main import app


@pytest.fixture
async def client():
    """Async test client for FastAPI."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        yield ac
