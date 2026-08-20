"""Natural-language lab-metric query — rules first, LLM only as fallback parser."""

from __future__ import annotations

import json
import os
import re
from dataclasses import dataclass, field
from datetime import date, datetime
from typing import Any, Literal

from sqlalchemy.ext.asyncio import AsyncSession

from chronocare.config import settings
from chronocare.models.medical_record import MedicalRecord
from chronocare.models.person import Person
from chronocare.services.lab_aliases import (
    METRIC_ALIAS_PAIRS,
    PERSON_ALIAS_PAIRS,
    PERSON_ALIASES,
    canonical_metric_names,
    normalize_text,
)
from chronocare.services.medical_record import list_medical_records
from chronocare.services.person import list_persons

TIME_LATEST_WORDS = (
    "最近一次",
    "上一次",
    "最新一次",
    "最近",
    "上次",
    "最新",
    "latest",
    "last",
)

STOP_WORDS = (
    *TIME_LATEST_WORDS,
    "怎么样",
    "如何",
    "情况",
    "是多少",
    "查一下",
    "看看",
    "告诉我",
    "请问",
    "帮我查",
    "帮我",
    "查询",
    "指标",
    "化验",
    "检验",
    "报告",
    "结果",
    "的",
    "是",
    "吗",
    "呢",
    "啊",
)

STATUS_LABEL = {
    "normal": "正常",
    "high": "偏高",
    "low": "偏低",
    "slightly_high": "轻微偏高",
    "slightly_low": "轻微偏低",
}

_DATE_PATTERNS = (
    re.compile(r"(20\d{2})[-/.](\d{1,2})[-/.](\d{1,2})"),
    re.compile(r"(20\d{2})年(\d{1,2})月(\d{1,2})日?"),
    re.compile(r"(20\d{2})年(\d{1,2})月"),
)


@dataclass
class QueryIntent:
    raw: str
    person_key: str | None = None
    person_id: int | None = None
    person_name: str | None = None
    metric: str | None = None
    time_mode: Literal["latest", "on_date", "in_month"] = "latest"
    on_date: date | None = None
    year: int | None = None
    month: int | None = None
    parser: str = "rules"
    inferred_person: bool = False


@dataclass
class LabHit:
    person_id: int
    person_name: str
    record_id: int
    visit_date: date | None
    hospital: str | None
    department: str | None
    test_name: str
    value: str
    unit: str
    reference: str
    status: str
    record_type: str


@dataclass
class LabQueryResult:
    intent: QueryIntent
    hit: LabHit | None = None
    previous: LabHit | None = None
    analysis: str = ""
    message: str = ""
    ok: bool = False
    candidates: list[LabHit] = field(default_factory=list)


def _strip_tokens(text: str, tokens: tuple[str, ...]) -> str:
    out = text
    for token in sorted(tokens, key=len, reverse=True):
        out = re.sub(re.escape(token), " ", out, flags=re.IGNORECASE)
    return re.sub(r"\s+", " ", out).strip()


def parse_time(text: str) -> tuple[Literal["latest", "on_date", "in_month"], date | None, int | None, int | None]:
    for pat in _DATE_PATTERNS:
        m = pat.search(text)
        if not m:
            continue
        groups = m.groups()
        year = int(groups[0])
        month = int(groups[1])
        if len(groups) == 3 and groups[2]:
            day = int(groups[2])
            try:
                return "on_date", date(year, month, day), year, month
            except ValueError:
                return "in_month", None, year, month
        return "in_month", None, year, month
    if any(word in text for word in TIME_LATEST_WORDS):
        return "latest", None, None, None
    return "latest", None, None, None


def find_person_key(text: str) -> str | None:
    norm = normalize_text(text)
    for alias, canonical in PERSON_ALIAS_PAIRS:
        if alias and alias in norm:
            return canonical
    return None


def find_metric(text: str) -> str | None:
    norm = normalize_text(text)
    if not norm:
        return None
    for alias, canonical in METRIC_ALIAS_PAIRS:
        if alias and alias in norm:
            return canonical
    return None


def parse_intent_rules(text: str) -> QueryIntent:
    person_key = find_person_key(text)
    time_mode, on_date, year, month = parse_time(text)
    remainder = text
    if person_key:
        remainder = _strip_tokens(remainder, PERSON_ALIASES.get(person_key, (person_key,)))
    remainder = _strip_tokens(remainder, STOP_WORDS)
    metric = find_metric(remainder) or find_metric(text)
    return QueryIntent(
        raw=text,
        person_key=person_key,
        metric=metric,
        time_mode=time_mode,
        on_date=on_date,
        year=year,
        month=month,
        parser="rules",
    )


def _metric_score(query_metric: str, test_name: str) -> int:
    q = normalize_text(query_metric)
    n = normalize_text(test_name)
    if not q or not n:
        return 0
    if q == n:
        return 100
    # Prefer the stored name containing the canonical/alias, not the reverse
    # (avoids "蛋白" swallowing "尿微量白蛋白" equally).
    if q in n:
        return 80 + min(len(q), 15)
    if n in q:
        return 60 + min(len(n), 15)
    return 0


def _as_date(value: Any) -> date | None:
    if value is None:
        return None
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    if isinstance(value, str):
        try:
            return date.fromisoformat(value[:10])
        except ValueError:
            return None
    return None


def _tests_of(record: MedicalRecord) -> list[dict[str, Any]]:
    data = record.lab_results
    if not isinstance(data, dict):
        return []
    tests = data.get("tests")
    if not isinstance(tests, list):
        return []
    return [t for t in tests if isinstance(t, dict) and (t.get("name") or "").strip()]


def _hit_from(record: MedicalRecord, person: Person, test: dict[str, Any]) -> LabHit:
    return LabHit(
        person_id=person.id,
        person_name=person.name,
        record_id=record.id,
        visit_date=_as_date(record.visit_date),
        hospital=record.hospital,
        department=record.department,
        test_name=str(test.get("name") or ""),
        value=str(test.get("value") or ""),
        unit=str(test.get("unit") or ""),
        reference=str(test.get("reference") or ""),
        status=str(test.get("status") or ""),
        record_type=record.record_type,
    )


def _filter_by_time(hits: list[LabHit], intent: QueryIntent) -> list[LabHit]:
    if intent.time_mode == "on_date" and intent.on_date:
        exact = [h for h in hits if h.visit_date == intent.on_date]
        return exact
    if intent.time_mode == "in_month" and intent.year and intent.month:
        return [
            h
            for h in hits
            if h.visit_date and h.visit_date.year == intent.year and h.visit_date.month == intent.month
        ]
    return hits


def _sort_hits(hits: list[LabHit]) -> list[LabHit]:
    return sorted(hits, key=lambda h: h.visit_date or date.min, reverse=True)


def _to_float(value: str) -> float | None:
    m = re.search(r"-?\d+(?:\.\d+)?", value.replace(",", ""))
    if not m:
        return None
    try:
        return float(m.group(0))
    except ValueError:
        return None


def build_analysis(hit: LabHit, previous: LabHit | None, inferred_person: bool) -> str:
    status = STATUS_LABEL.get(hit.status, hit.status or "未知")
    unit = hit.unit.strip()
    if unit and unit not in hit.value:
        value_text = f"{hit.value}{unit}" if unit.startswith("%") else f"{hit.value} {unit}"
    else:
        value_text = hit.value
    date_text = hit.visit_date.isoformat() if hit.visit_date else "日期不详"
    parts = [
        f"{hit.person_name} 在 {date_text} 的「{hit.test_name}」为 {value_text}，状态：{status}。",
    ]
    if inferred_person:
        parts.append(f"未指定人员，已按 {hit.person_name} 的化验查询。")
    if hit.reference and hit.reference not in ("None", "null"):
        parts.append(f"参考范围：{hit.reference}。")
    if previous and previous.visit_date:
        prev_unit = previous.unit.strip()
        if prev_unit and prev_unit not in previous.value:
            prev_val = f"{previous.value}{prev_unit}" if prev_unit.startswith("%") else f"{previous.value} {prev_unit}"
        else:
            prev_val = previous.value
        curr_n = _to_float(hit.value)
        prev_n = _to_float(previous.value)
        trend = ""
        if curr_n is not None and prev_n is not None and prev_n != 0:
            delta = curr_n - prev_n
            if abs(delta) < 1e-9:
                trend = "，与上次基本持平"
            elif delta > 0:
                trend = f"，较 {previous.visit_date.isoformat()} 的 {prev_val} 上升"
            else:
                trend = f"，较 {previous.visit_date.isoformat()} 的 {prev_val} 下降"
        else:
            trend = f"，上次（{previous.visit_date.isoformat()}）为 {prev_val}"
        parts.append(trend.lstrip("，") + "。")
    if hit.status in {"high", "low", "slightly_high", "slightly_low"}:
        parts.append("建议结合临床表现咨询主治医生，本结果不能替代医嘱。")
    return "".join(parts)


def _call_llm_intent(query: str) -> dict[str, Any] | None:
    """Best-effort intent extraction. Returns None if LLM is unavailable."""
    import httpx

    api_key = settings.llm_api_key or os.environ.get("OPENROUTER_API_KEY", "")
    if not api_key:
        return None
    metrics = "、".join(canonical_metric_names())
    prompt = (
        "你是化验指标查询的意图解析器。只输出 JSON，不要解释。\n"
        "人员只能是 qian 或 tjh 或 null。\n"
        f"指标必须是下列之一或 null：{metrics}\n"
        '格式：{"person":"qian"|"tjh"|null,"metric":"指标名或null","date":"YYYY-MM-DD或null","latest":true|false}\n'
        f"用户问：{query}\n"
    )
    payload = {
        "model": settings.llm_model,
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": 256,
    }
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    try:
        with httpx.Client(timeout=20.0) as client:
            response = client.post(
                "https://openrouter.ai/api/v1/chat/completions",
                headers=headers,
                json=payload,
            )
            response.raise_for_status()
            content = response.json()["choices"][0]["message"]["content"]
    except Exception:
        return None
    cleaned = content.strip()
    cleaned = re.sub(r"^```(?:json)?\s*", "", cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r"\s*```$", "", cleaned)
    try:
        start = cleaned.find("{")
        end = cleaned.rfind("}") + 1
        return json.loads(cleaned[start:end])
    except (json.JSONDecodeError, ValueError):
        return None


def merge_llm_intent(intent: QueryIntent, llm: dict[str, Any]) -> QueryIntent:
    person = llm.get("person")
    if not intent.person_key and person in {"qian", "tjh"}:
        intent.person_key = person
    metric = llm.get("metric")
    if not intent.metric and isinstance(metric, str) and metric.strip():
        intent.metric = find_metric(metric) or metric.strip()
    date_s = llm.get("date")
    if not intent.on_date and isinstance(date_s, str):
        try:
            intent.on_date = date.fromisoformat(date_s[:10])
            intent.time_mode = "on_date"
        except ValueError:
            pass
    intent.parser = "rules+llm"
    return intent


def resolve_person(persons: list[Person], person_key: str | None) -> Person | None:
    if not person_key:
        return None
    key = normalize_text(person_key)
    for person in persons:
        if normalize_text(person.name) == key:
            return person
        aliases = PERSON_ALIASES.get(person.name.lower(), ())
        if key in {normalize_text(a) for a in aliases}:
            return person
    return None


async def run_lab_query(
    db: AsyncSession,
    query: str,
    *,
    allow_llm: bool = True,
    llm_fn=None,
) -> LabQueryResult:
    text = (query or "").strip()
    if not text:
        return LabQueryResult(
            intent=QueryIntent(raw=""),
            message="请输入要查询的人员、指标，例如：qian 最近一次糖化血红蛋白怎么样",
        )

    intent = parse_intent_rules(text)
    persons = await list_persons(db)

    if allow_llm and not intent.metric:
        llm_fn = llm_fn or _call_llm_intent
        llm_data = llm_fn(text)
        if llm_data:
            intent = merge_llm_intent(intent, llm_data)

    person = resolve_person(persons, intent.person_key)
    if intent.person_key and person is None:
        return LabQueryResult(intent=intent, message=f"找不到人员「{intent.person_key}」。目前档案是 qian / tjh。")

    if person is None:
        # Default to the person who actually has structured labs.
        lab_owners: list[Person] = []
        for p in persons:
            recs = await list_medical_records(db, person_id=p.id, record_type="lab_report")
            if any(_tests_of(r) for r in recs):
                lab_owners.append(p)
        if len(lab_owners) == 1:
            person = lab_owners[0]
            intent.person_id = person.id
            intent.person_name = person.name
            intent.inferred_person = True
        elif not lab_owners:
            return LabQueryResult(intent=intent, message="目前没有任何结构化化验结果可查询。")
        else:
            return LabQueryResult(intent=intent, message="请指定要查询的人员，例如：qian 或 妈妈。")
    else:
        intent.person_id = person.id
        intent.person_name = person.name

    records = await list_medical_records(db, person_id=person.id, record_type="lab_report")
    if not any(_tests_of(r) for r in records):
        return LabQueryResult(
            intent=intent,
            message=f"{person.name} 目前没有结构化化验报告可查询（只有已 OCR 并解析出检验项目的化验单才能检索）。",
        )

    if not intent.metric:
        return LabQueryResult(
            intent=intent,
            message="没能识别要查的指标。可以试试：糖化血红蛋白、肌酐、尿微量白蛋白、ALT。",
        )

    scored: list[tuple[int, LabHit]] = []
    for rec in records:
        for test in _tests_of(rec):
            score = _metric_score(intent.metric, str(test.get("name") or ""))
            if score <= 0:
                continue
            scored.append((score, _hit_from(rec, person, test)))
    if not scored:
        return LabQueryResult(
            intent=intent,
            message=f"在 {person.name} 的化验单里没有找到「{intent.metric}」。",
        )

    best = max(s for s, _ in scored)
    matched = _sort_hits([h for s, h in scored if s == best])
    timed = _filter_by_time(matched, intent)
    if intent.time_mode in {"on_date", "in_month"} and not timed:
        return LabQueryResult(
            intent=intent,
            message=f"找到了「{intent.metric}」，但指定时间没有记录。最近一次是 {_fmt_hit(matched[0])}。",
            candidates=matched[:3],
        )

    pool = timed or matched
    hit = pool[0]
    previous = pool[1] if len(pool) > 1 else None
    # previous should be strictly older than hit, even if time filter collapsed
    if previous is None:
        older = [
            h
            for h in matched
            if h.record_id != hit.record_id and (h.visit_date or date.min) < (hit.visit_date or date.min)
        ]
        previous = older[0] if older else None

    analysis = build_analysis(hit, previous, intent.inferred_person)
    return LabQueryResult(
        intent=intent,
        hit=hit,
        previous=previous,
        analysis=analysis,
        ok=True,
        message="",
    )


def _fmt_hit(hit: LabHit) -> str:
    when = hit.visit_date.isoformat() if hit.visit_date else "日期不详"
    unit = hit.unit.strip()
    value = f"{hit.value}{unit}" if unit and unit not in hit.value else hit.value
    return f"{when} {value}"


def result_to_dict(result: LabQueryResult) -> dict[str, Any]:
    def hit_dict(hit: LabHit | None) -> dict[str, Any] | None:
        if hit is None:
            return None
        return {
            "person_id": hit.person_id,
            "person_name": hit.person_name,
            "record_id": hit.record_id,
            "visit_date": hit.visit_date.isoformat() if hit.visit_date else None,
            "hospital": hit.hospital,
            "department": hit.department,
            "test_name": hit.test_name,
            "value": hit.value,
            "unit": hit.unit,
            "reference": hit.reference,
            "status": hit.status,
            "status_label": STATUS_LABEL.get(hit.status, hit.status),
            "preview_url": f"/medical-records/{hit.record_id}/preview",
            "file_url": f"/medical-records/{hit.record_id}/file",
            "detail_url": f"/medical-records/{hit.record_id}",
        }

    return {
        "ok": result.ok,
        "message": result.message,
        "analysis": result.analysis,
        "parser": result.intent.parser,
        "query": result.intent.raw,
        "metric": result.intent.metric,
        "person": result.intent.person_name,
        "hit": hit_dict(result.hit),
        "previous": hit_dict(result.previous),
    }
