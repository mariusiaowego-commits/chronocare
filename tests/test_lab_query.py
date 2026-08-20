"""Lab NL query parser + lookup."""

import pytest

from chronocare.database import async_session_factory
from chronocare.services.lab_query import (
    find_metric,
    find_person_key,
    parse_intent_rules,
    run_lab_query,
)


def test_parse_hba1c_latest():
    intent = parse_intent_rules("qian 最近一次糖化血红蛋白怎么样")
    assert intent.person_key == "qian"
    assert intent.metric == "糖化血红蛋白"
    assert intent.time_mode == "latest"


def test_aliases_person_and_metric():
    assert find_person_key("妈妈上次肌酐") == "qian"
    assert find_person_key("tjh 糖化") == "tjh"
    assert find_metric("HbA1c") == "糖化血红蛋白"
    assert find_metric("糖化") == "糖化血红蛋白"
    assert find_metric("ALT") == "丙氨酸氨基转移酶"
    assert find_metric("肌酐") == "肌酐"


def test_parse_iso_date():
    intent = parse_intent_rules("qian 2025-12-30 ALT")
    assert intent.person_key == "qian"
    assert intent.metric == "丙氨酸氨基转移酶"
    assert intent.time_mode == "on_date"
    assert str(intent.on_date) == "2025-12-30"


def test_unknown_metric_rules():
    intent = parse_intent_rules("qian 最近一次飞行速度")
    assert intent.person_key == "qian"
    assert intent.metric is None


@pytest.mark.asyncio
async def test_query_hba1c_from_db():
    async with async_session_factory() as db:
        def boom(_query: str):
            raise AssertionError("LLM should not run when rules match")

        result = await run_lab_query(db, "qian 最近一次糖化血红蛋白怎么样", llm_fn=boom)
        assert result.ok
        assert result.hit is not None
        assert "7.8" in result.hit.value
        assert result.hit.test_name == "糖化血红蛋白"
        assert result.hit.record_id == 5
        assert "偏高" in result.analysis
        assert "4.0" in result.analysis or "参考" in result.analysis


@pytest.mark.asyncio
async def test_query_latest_alt_has_previous():
    async with async_session_factory() as db:
        result = await run_lab_query(db, "qian 最近一次 ALT", allow_llm=False)
        assert result.ok
        assert result.hit is not None
        assert result.hit.value == "12"
        assert result.previous is not None
        assert result.previous.value == "7"


@pytest.mark.asyncio
async def test_query_tjh_has_no_structured_labs():
    async with async_session_factory() as db:
        result = await run_lab_query(db, "tjh 最近一次糖化血红蛋白", allow_llm=False)
        assert result.ok is False
        assert result.hit is None
        assert "没有" in result.message or "结构化" in result.message


@pytest.mark.asyncio
async def test_query_missing_metric_message():
    async with async_session_factory() as db:
        result = await run_lab_query(db, "qian 最近一次飞行速度", allow_llm=False)
        assert result.ok is False
        assert "没有找到" in result.message


@pytest.mark.asyncio
async def test_query_real_names_not_just_aliases():
    async with async_session_factory() as db:
        chol = await run_lab_query(db, "胆固醇", allow_llm=False)
        assert chol.ok
        assert chol.hit is not None
        assert chol.hit.test_name == "总胆固醇"

        tg = await run_lab_query(db, "甘油三酯", allow_llm=False)
        assert tg.ok and tg.hit is not None
        assert tg.hit.test_name == "甘油三酯"

        ga = await run_lab_query(db, "糖化白蛋白", allow_llm=False)
        assert ga.ok and ga.hit is not None
        assert ga.hit.test_name == "糖化白蛋白"

        fbg = await run_lab_query(db, "空腹血糖", allow_llm=False)
        assert fbg.ok and fbg.hit is not None
        assert "空腹" in fbg.hit.test_name

        wbc = await run_lab_query(db, "白细胞", allow_llm=False)
        assert wbc.ok and wbc.hit is not None
        assert wbc.hit.test_name == "白细胞计数"
        assert "10^9" in (wbc.hit.unit or "") or "10⁹" in (wbc.hit.unit or "")

        k = await run_lab_query(db, "钾", allow_llm=False)
        assert k.ok and k.hit is not None
        assert k.hit.test_name == "钾"


@pytest.mark.asyncio
async def test_query_panels_and_overview():
    async with async_session_factory() as db:
        liver = await run_lab_query(db, "妈妈肝功能", allow_llm=False)
        assert liver.ok
        assert liver.kind == "panel"
        names = {h.test_name for h in liver.hits}
        assert "丙氨酸氨基转移酶" in names
        assert "肌酐" not in names

        lipids = await run_lab_query(db, "血脂", allow_llm=False)
        assert lipids.ok and lipids.kind == "panel"
        lipid_names = {h.test_name for h in lipids.hits}
        assert "总胆固醇" in lipid_names
        assert "甘油三酯" in lipid_names

        overview = await run_lab_query(db, "钱精华最近一次化验", allow_llm=False)
        assert overview.ok
        assert overview.kind == "overview"
        assert len(overview.hits) >= 3

        bp = await run_lab_query(db, "血压", allow_llm=False)
        assert bp.ok is False
        assert "不在化验单" in bp.message


@pytest.mark.asyncio
async def test_api_and_page(client):
    api = await client.get("/api/lab-query", params={"q": "qian 最近一次糖化血红蛋白怎么样"})
    assert api.status_code == 200
    body = api.json()
    assert body["ok"] is True
    assert body["hit"]["value"] == "7.8"
    assert body["hit"]["preview_url"] == "/medical-records/5/preview"

    page = await client.get("/query", params={"q": "qian 最近一次糖化血红蛋白怎么样"})
    assert page.status_code == 200
    html = page.text
    assert "7.8" in html
    assert "糖化血红蛋白" in html
    assert "/medical-records/5/preview" in html
    assert "来源化验单" in html
