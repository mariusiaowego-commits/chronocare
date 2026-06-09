"""Tests for report generation API endpoints."""

from __future__ import annotations

import pytest
from httpx import AsyncClient


@pytest.fixture
async def person_id(client: AsyncClient) -> int:
    """Create a test person and return its ID."""
    resp = await client.post(
        "/api/persons",
        json={"name": "测试报告人物", "gender": "M"},
    )
    assert resp.status_code == 201
    return resp.json()["id"]


@pytest.mark.anyio
async def test_generate_report_creates_pending_record(
    client: AsyncClient, person_id: int
):
    """POST /api/persons/{id}/reports/generate should create a pending record."""
    resp = await client.post(
        f"/api/persons/{person_id}/reports/generate",
        json={"layout": "pc"},
    )
    assert resp.status_code == 202
    data = resp.json()
    assert data["person_id"] == person_id
    assert data["layout"] == "pc"
    assert data["status"] == "pending"
    assert "id" in data


@pytest.mark.anyio
async def test_generate_report_mobile_layout(client: AsyncClient, person_id: int):
    """Should support mobile layout."""
    resp = await client.post(
        f"/api/persons/{person_id}/reports/generate",
        json={"layout": "mobile"},
    )
    assert resp.status_code == 202
    assert resp.json()["layout"] == "mobile"


@pytest.mark.anyio
async def test_generate_report_nonexistent_person(client: AsyncClient):
    """Should return 404 for nonexistent person."""
    resp = await client.post(
        "/api/persons/99999/reports/generate",
        json={"layout": "pc"},
    )
    assert resp.status_code == 404


@pytest.mark.anyio
async def test_get_report_status(client: AsyncClient, person_id: int):
    """GET /api/reports/{id} should return the report record."""
    # Create
    create_resp = await client.post(
        f"/api/persons/{person_id}/reports/generate",
        json={"layout": "pc"},
    )
    report_id = create_resp.json()["id"]

    # Get
    resp = await client.get(f"/api/reports/{report_id}")
    assert resp.status_code == 200
    assert resp.json()["id"] == report_id


@pytest.mark.anyio
async def test_get_report_not_found(client: AsyncClient):
    """Should return 404 for nonexistent report."""
    resp = await client.get("/api/reports/99999")
    assert resp.status_code == 404


@pytest.mark.anyio
async def test_list_person_reports(client: AsyncClient, person_id: int):
    """GET /api/persons/{id}/reports should return report list."""
    # Generate 2 reports
    await client.post(
        f"/api/persons/{person_id}/reports/generate",
        json={"layout": "pc"},
    )
    await client.post(
        f"/api/persons/{person_id}/reports/generate",
        json={"layout": "mobile"},
    )

    resp = await client.get(f"/api/persons/{person_id}/reports")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 2
    layouts = {r["layout"] for r in data}
    assert layouts == {"pc", "mobile"}


@pytest.mark.anyio
async def test_list_reports_empty(client: AsyncClient, person_id: int):
    """Should return empty list when no reports exist."""
    resp = await client.get(f"/api/persons/{person_id}/reports")
    assert resp.status_code == 200
    assert resp.json() == []


@pytest.mark.anyio
async def test_report_data_aggregation(client: AsyncClient, person_id: int):
    """Aggregated data should include person info even with no visits."""
    from chronocare.services.report_data import aggregate_person_data
    from chronocare.database import async_session_factory

    async with async_session_factory() as db:
        data = await aggregate_person_data(db, person_id)
        assert data["person"]["name"] == "测试报告人物"
        assert data["summary"]["visit_count"] == 0
        assert data["summary"]["record_count"] == 0
        assert data["blood_sugar"]["records"] == []
