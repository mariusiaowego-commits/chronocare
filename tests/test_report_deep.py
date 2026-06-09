"""Deep verification tests for health report feature."""

from __future__ import annotations

from unittest.mock import AsyncMock, patch

import pytest
from httpx import AsyncClient

from chronocare.services.report_data import (
    aggregate_person_data,
    parse_diagnosis,
    normalize_diag,
    extract_doctor,
)
from chronocare.services.report_generation import _build_prompt


# ── Pure function tests ──


class TestParseDiagnosis:
    def test_basic(self):
        assert parse_diagnosis("1.心房颤动 2.高血压") == ["心房颤动", "高血压"]

    def test_with_prefix(self):
        assert parse_diagnosis("西医诊断:1.心房颤动 2.二尖瓣关闭不全") == [
            "心房颤动",
            "二尖瓣关闭不全",
        ]

    def test_empty(self):
        assert parse_diagnosis(None) == []
        assert parse_diagnosis("") == []

    def test_single(self):
        assert parse_diagnosis("1.失眠") == ["失眠"]


class TestNormalizeDiag:
    def test_insomnia(self):
        assert normalize_diag("失眠症") == "失眠"
        assert normalize_diag("睡眠障碍") == "失眠"

    def test_normal(self):
        assert normalize_diag("心房颤动") == "心房颤动"


class TestExtractDoctor:
    def test_none_input(self):
        assert extract_doctor(None) is None
        assert extract_doctor("") is None

    def test_with_known_doctors(self):
        text = "some text 张培培 1/5 some more text"
        assert extract_doctor(text, known_doctors={"张培培"}) == "张培培"

    def test_blacklist_filter(self):
        text = "some text 随访 复查 1/5"
        assert extract_doctor(text) is None


# ── Prompt building tests ──


class TestPromptBuilding:
    def _make_minimal_data(self):
        return {
            "person": {
                "id": 1,
                "name": "测试",
                "gender": "M",
                "birth_date": "1950-01-01",
            },
            "summary": {
                "visit_count": 5,
                "record_count": 3,
                "blood_sugar_count": 0,
                "date_range": ["2024-01-01", "2024-12-31"],
            },
            "doctors": {
                "high_frequency": ["张医生"],
                "single_hit_candidates": [],
                "no_doctor_pdfs": 0,
                "details": {
                    "张医生": {
                        "pdf_count": 3,
                        "visit_days": 3,
                        "visit_dates": ["2024-01-01"],
                        "diagnoses": ["心房颤动"],
                    }
                },
            },
            "diagnosis_consistency": {
                "all_diagnoses": ["心房颤动"],
                "common_across_doctors": ["心房颤动"],
                "by_doctor": {
                    "张医生": {
                        "diagnoses": ["心房颤动"],
                        "diff": {"only_this": [], "only_others": []},
                    }
                },
            },
            "blood_sugar": {"records": [], "summary": {}},
            "key_metrics": {"inr_values": [], "echo_findings": []},
        }

    def test_pc_prompt_contains_required_elements(self):
        data = self._make_minimal_data()
        prompt = _build_prompt(data, "pc")
        assert "morandi-journal" in prompt
        assert "winding-roadmap" in prompt
        assert "#F5F0E6" in prompt
        assert "#8FA876" in prompt
        assert "#D4956A" in prompt
        assert "测试" in prompt
        assert "心房颤动" in prompt
        assert "portrait" in prompt

    def test_mobile_prompt_contains_required_elements(self):
        data = self._make_minimal_data()
        prompt = _build_prompt(data, "mobile")
        assert "morandi-journal" in prompt
        assert "#F5F0E6" in prompt

    def test_pc_prompt_forbids_red(self):
        data = self._make_minimal_data()
        prompt = _build_prompt(data, "pc")
        assert "NOT red" in prompt

    def test_empty_date_range(self):
        data = self._make_minimal_data()
        data["summary"]["date_range"] = []
        prompt = _build_prompt(data, "pc")
        assert "未知" in prompt

    def test_empty_doctors(self):
        data = self._make_minimal_data()
        data["doctors"]["details"] = {}
        prompt = _build_prompt(data, "pc")
        assert "暂无" in prompt


# ── API integration tests ──


@pytest.fixture
async def person_id(client: AsyncClient) -> int:
    resp = await client.post(
        "/api/persons", json={"name": "深度验证人物", "gender": "F"}
    )
    assert resp.status_code == 201
    return resp.json()["id"]


@pytest.mark.anyio
@patch(
    "chronocare.routers.api.report.svc.generate_report", new_callable=AsyncMock
)
async def test_api_generate_schema(mock_gen, client: AsyncClient, person_id: int):
    resp = await client.post(
        f"/api/persons/{person_id}/reports/generate", json={"layout": "pc"}
    )
    data = resp.json()
    assert resp.status_code == 202
    assert "id" in data
    assert data["person_id"] == person_id
    assert data["layout"] == "pc"
    assert data["status"] == "pending"
    assert "created_at" in data


@pytest.mark.anyio
async def test_api_nonexistent_person_404(client: AsyncClient):
    resp = await client.post(
        "/api/persons/99999/reports/generate", json={"layout": "pc"}
    )
    assert resp.status_code == 404


@pytest.mark.anyio
async def test_report_history_empty(client: AsyncClient, person_id: int):
    resp = await client.get(f"/api/persons/{person_id}/reports")
    assert resp.status_code == 200
    assert resp.json() == []


@pytest.mark.anyio
async def test_report_status_nonexistent(client: AsyncClient):
    resp = await client.get("/api/reports/99999")
    assert resp.status_code == 404
