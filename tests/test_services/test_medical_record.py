"""End-to-end tests for medical record OCR pipeline."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from httpx import AsyncClient

from chronocare.database import get_db
from chronocare.main import app

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


async def create_record(client: AsyncClient, person_id: int, record_type: str, **kwargs):
    """Create a medical record and return the JSON."""
    payload = {
        "person_id": person_id,
        "record_type": record_type,
        "hospital": kwargs.get("hospital", "测试医院"),
        "department": kwargs.get("department", "内分泌科"),
        "doctor": kwargs.get("doctor", "张医生"),
        "visit_date": kwargs.get("visit_date", "2026-05-13"),
        **kwargs,
    }
    resp = await client.post("/api/medical-records", json=payload)
    assert resp.status_code == 201, resp.text
    return resp.json()


# ---------------------------------------------------------------------------
# CRUD — 4 record types
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
@pytest.mark.parametrize("record_type", [
    "medical_record",
    "lab_report",
    "prescription",
    "doctor_order",
])
async def test_create_and_get_record_type(client: AsyncClient, create_person, record_type: str):
    """Create a record for each type and retrieve it."""
    pid = create_person["id"]
    record = await create_record(client, pid, record_type)
    assert record["record_type"] == record_type
    assert record["hospital"] == "测试医院"

    resp = await client.get(f"/api/medical-records/{record['id']}")
    assert resp.status_code == 200
    assert resp.json()["record_type"] == record_type


@pytest.mark.asyncio
async def test_list_records_filtered_by_type(client: AsyncClient, create_person):
    """List endpoint filters by record_type."""
    pid = create_person["id"]
    await create_record(client, pid, "lab_report")
    await create_record(client, pid, "doctor_order")
    await create_record(client, pid, "medical_record")

    resp = await client.get("/api/medical-records", params={"person_id": pid, "record_type": "lab_report"})
    assert resp.status_code == 200
    rows = resp.json()
    assert all(r["record_type"] == "lab_report" for r in rows)


@pytest.mark.asyncio
async def test_update_record(client: AsyncClient, create_person):
    """PATCH updates fields correctly."""
    record = await create_record(client, create_person["id"], "medical_record", hospital="旧医院")
    resp = await client.patch(f"/api/medical-records/{record['id']}", json={"hospital": "新医院"})
    assert resp.status_code == 200
    assert resp.json()["hospital"] == "新医院"


@pytest.mark.asyncio
async def test_delete_record(client: AsyncClient, create_person):
    """DELETE removes the record."""
    record = await create_record(client, create_person["id"], "medical_record")
    resp = await client.delete(f"/api/medical-records/{record['id']}")
    assert resp.status_code == 204

    resp = await client.get(f"/api/medical-records/{record['id']}")
    assert resp.status_code == 404


# ---------------------------------------------------------------------------
# Error scenarios
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_ocr_no_image_returns_error(client: AsyncClient, create_person):
    """process-ocr returns 400 when no image is uploaded."""
    record = await create_record(client, create_person["id"], "medical_record")
    resp = await client.post(f"/api/medical-records/{record['id']}/ocr")
    assert resp.status_code == 400
    assert "image" in resp.json()["detail"].lower()


@pytest.mark.asyncio
async def test_ocr_unavailable_returns_friendly_error(client: AsyncClient, create_person):
    """When OCR is unavailable, API returns friendly 400 (not 500)."""
    record = await create_record(client, create_person["id"], "medical_record")

    from chronocare.models.medical_record import MedicalRecord

    fake_record = MagicMock(spec=MedicalRecord)
    fake_record.id = record["id"]
    fake_record.person_id = create_person["id"]
    fake_record.image_path = "/tmp/fake_ocr_test.png"
    fake_record.ocr_text = None
    fake_record.structured_data = None

    mock_session = MagicMock()
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = fake_record
    mock_session.execute = AsyncMock(return_value=mock_result)
    mock_session.commit = AsyncMock()
    mock_session.refresh = AsyncMock()

    async def mock_get_db():
        yield mock_session

    app.dependency_overrides[get_db] = mock_get_db
    try:
        with patch("chronocare.services.medical_record.is_ocr_available", new_callable=AsyncMock) as mock_avail:
            mock_avail.return_value = False
            resp = await client.post(f"/api/medical-records/{record['id']}/ocr")
            assert resp.status_code == 400
            assert "不可用" in resp.json()["detail"] or "Swift" in resp.json()["detail"]
    finally:
        app.dependency_overrides.pop(get_db, None)


@pytest.mark.asyncio
async def test_process_lab_no_image_returns_error(client: AsyncClient, create_person):
    """process-lab returns 400 when no image is uploaded."""
    record = await create_record(client, create_person["id"], "lab_report")
    resp = await client.post(f"/api/medical-records/{record['id']}/process-lab")
    assert resp.status_code == 400
    assert "image" in resp.json()["detail"].lower()


@pytest.mark.asyncio
async def test_process_order_no_image_returns_error(client: AsyncClient, create_person):
    """process-order returns 400 when no image is uploaded."""
    record = await create_record(client, create_person["id"], "doctor_order")
    resp = await client.post(f"/api/medical-records/{record['id']}/process-order")
    assert resp.status_code == 400
    assert "image" in resp.json()["detail"].lower()


@pytest.mark.asyncio
async def test_get_nonexistent_record_returns_404(client: AsyncClient):
    """GET /api/medical-records/99999 → 404."""
    resp = await client.get("/api/medical-records/99999")
    assert resp.status_code == 404


# ---------------------------------------------------------------------------
# OCR service error handling — no API key gracefully handled (not 500)
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_ocr_no_api_key_returns_error_in_body_not_500(client: AsyncClient, create_person):
    """When Swift_API_KEY is missing, error appears in response body (friendly handling)."""
    record = await create_record(client, create_person["id"], "medical_record")

    from chronocare.models.medical_record import MedicalRecord

    fake_record = MagicMock(spec=MedicalRecord)
    fake_record.id = record["id"]
    fake_record.person_id = create_person["id"]
    fake_record.image_path = "/tmp/fake_ocr_test.png"
    fake_record.ocr_text = None
    fake_record.structured_data = None

    mock_session = MagicMock()
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = fake_record
    mock_session.execute = AsyncMock(return_value=mock_result)
    mock_session.commit = AsyncMock()
    mock_session.refresh = AsyncMock()

    async def mock_get_db():
        yield mock_session

    app.dependency_overrides[get_db] = mock_get_db
    try:
        with patch(
            "chronocare.services.medical_record.is_ocr_available", new_callable=AsyncMock
        ) as mock_avail, patch(
            "chronocare.services.medical_record.extract_text", new_callable=AsyncMock
        ) as mock_extract, patch(
            "chronocare.services.medical_record.parse_ocr_text", new_callable=AsyncMock
        ) as mock_parse:
            mock_avail.return_value = True
            mock_extract.return_value = "这是一段测试OCR文字"
            mock_parse.return_value = {"error": "Swift_API_KEY is not set"}

            resp = await client.post(f"/api/medical-records/{record['id']}/ocr")
            # OCR text is preserved even when LLM parsing fails
            assert resp.status_code == 200
            body = resp.json()
            assert "error" in body.get("structured_data", {})
            assert "Swift_API_KEY" in body["structured_data"]["error"]
    finally:
        app.dependency_overrides.pop(get_db, None)


# ---------------------------------------------------------------------------
# Unified /process endpoint
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_process_auto_routes_lab_report(client: AsyncClient, create_person):
    """POST /process routes lab_report → process_lab_report."""
    record = await create_record(client, create_person["id"], "lab_report")
    resp = await client.post(f"/api/medical-records/{record['id']}/process")
    assert resp.status_code == 400
    assert "image" in resp.json()["detail"].lower()


@pytest.mark.asyncio
async def test_process_auto_routes_doctor_order(client: AsyncClient, create_person):
    """POST /process routes doctor_order → process_doctor_order."""
    record = await create_record(client, create_person["id"], "doctor_order")
    resp = await client.post(f"/api/medical-records/{record['id']}/process")
    assert resp.status_code == 400
    assert "image" in resp.json()["detail"].lower()


@pytest.mark.asyncio
async def test_process_auto_routes_medical_record(client: AsyncClient, create_person):
    """POST /process routes medical_record → process_ocr."""
    record = await create_record(client, create_person["id"], "medical_record")
    resp = await client.post(f"/api/medical-records/{record['id']}/process")
    assert resp.status_code == 400
    assert "image" in resp.json()["detail"].lower()


# ---------------------------------------------------------------------------
# Fixture: create_person
# ---------------------------------------------------------------------------


@pytest.fixture
async def create_person(client: AsyncClient):
    """Create a test person once per test function."""
    resp = await client.post("/api/persons", json={
        "name": "测试人员",
        "gender": "M",
        "birth_date": "1960-01-01",
    })
    assert resp.status_code == 201
    return resp.json()
