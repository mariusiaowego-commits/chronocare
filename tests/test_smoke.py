"""Smoke tests for ChronoCare app."""

import pytest
from httpx import ASGITransport, AsyncClient

from chronocare.main import app


@pytest.mark.asyncio
async def test_health():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        resp = await client.get("/health")
        assert resp.status_code == 200
        assert resp.json()["status"] == "healthy"


@pytest.mark.asyncio
async def test_person_crud():
    """Test full Person CRUD cycle via API."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        # Create
        resp = await client.post("/api/persons", json={
            "name": "测试老人",
            "gender": "F",
            "birth_date": "1950-05-15",
            "height_cm": 160.0,
            "weight_kg": 55.0,
            "blood_type": "A",
        })
        assert resp.status_code == 201
        person = resp.json()
        pid = person["id"]
        assert person["name"] == "测试老人"
        assert person["gender"] == "F"

        # List
        resp = await client.get("/api/persons")
        assert resp.status_code == 200
        assert len(resp.json()) >= 1

        # Get
        resp = await client.get(f"/api/persons/{pid}")
        assert resp.status_code == 200
        assert resp.json()["birth_date"] == "1950-05-15"

        # Update
        resp = await client.patch(f"/api/persons/{pid}", json={"weight_kg": 58.0})
        assert resp.status_code == 200
        assert resp.json()["weight_kg"] == 58.0

        # Add condition
        resp = await client.post(f"/api/persons/{pid}/conditions", json={
            "name": "高血压",
            "status": "managed",
            "severity": "moderate",
        })
        assert resp.status_code == 201
        cond = resp.json()
        assert cond["name"] == "高血压"

        # List conditions
        resp = await client.get(f"/api/persons/{pid}/conditions")
        assert resp.status_code == 200
        assert len(resp.json()) == 1

        # Delete condition
        resp = await client.delete(f"/api/persons/conditions/{cond['id']}")
        assert resp.status_code == 204

        # Delete person
        resp = await client.delete(f"/api/persons/{pid}")
        assert resp.status_code == 204

        # Confirm deleted
        resp = await client.get(f"/api/persons/{pid}")
        assert resp.status_code == 404
