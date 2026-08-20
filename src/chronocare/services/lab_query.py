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
    PANELS,
    PERSON_ALIAS_PAIRS,
    PERSON_ALIASES,
    aliases_for_test,
    canonical_metric_names,
    find_panel,
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
    kind: str = "metric"  # metric | panel | overview
    hits: list[LabHit] = field(default_factory=list)
    suggestions: list[str] = field(default_factory=list)
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


MIN_SCORE = 70
_ABNORMAL = frozenset({"high", "low", "slightly_high", "slightly_low"})


def score_name(query_metric: str, test_name: str) -> int:
    """Score a user metric string against a stored lab item name."""
    q = normalize_text(query_metric)
    n = normalize_text(test_name)
    if not q or not n:
        return 0
    # Single CJK char (钾/钠): exact name only.
    if len(q) == 1:
        return 100 if q == n else 0

    best = 0
    if q == n:
        best = 100
    elif n.startswith(q):
        best = max(best, 88 + min(len(q), 10))
    elif q in n:
        best = max(best, 80 + min(len(q), 15))
    elif n in q:
        best = max(best, 74 + min(len(n), 12))

    for alias in (test_name, *aliases_for_test(test_name)):
        a = normalize_text(alias)
        if len(a) < 2:
            continue
        if a == q:
            best = max(best, 97)
        elif a in q:
            best = max(best, 70 + min(len(a), 15))
    return best


def _name_tiebreak(query_metric: str, test_name: str) -> tuple[int, int]:
    """Lower tuple wins: exact, suffix/总X, then shorter name."""
    q = normalize_text(query_metric)
    n = normalize_text(test_name)
    if q == n:
        return (0, len(n))
    if n == f"总{q}" or n.endswith(q):
        return (1, len(n))
    return (2, len(n))


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


def _is_urine_unit(unit: str) -> bool:
    u = (unit or "").lower().replace("μ", "u").replace("µ", "u")
    return "/ul" in u or "/hp" in u or "/hpf" in u


def _sort_hits(hits: list[LabHit]) -> list[LabHit]:
    """Latest date first; on the same day prefer blood units over urine /uL."""
    return sorted(
        hits,
        key=lambda h: (h.visit_date or date.min, not _is_urine_unit(h.unit), h.record_id),
        reverse=True,
    )


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


def _catalog(records: list[MedicalRecord], person: Person) -> list[LabHit]:
    hits: list[LabHit] = []
    for rec in records:
        for test in _tests_of(rec):
            hits.append(_hit_from(rec, person, test))
    return hits


def _metric_remainder(text: str, person_key: str | None) -> str:
    remainder = text
    if person_key:
        remainder = _strip_tokens(remainder, PERSON_ALIASES.get(person_key, (person_key,)))
    remainder = _strip_tokens(remainder, STOP_WORDS)
    return remainder.strip(" ，,。.?？")


def _unique_names(hits: list[LabHit]) -> list[str]:
    seen: list[str] = []
    for hit in hits:
        if hit.test_name not in seen:
            seen.append(hit.test_name)
    return seen


_PREFERRED_SUGGESTIONS = (
    "糖化血红蛋白",
    "葡萄糖（空腹）",
    "肌酐",
    "总胆固醇",
    "甘油三酯",
    "白细胞计数",
    "血红蛋白浓度",
    "尿微量白蛋白",
    "丙氨酸氨基转移酶",
    "钾",
)

_VITALS = {
    "血压": "血压不在化验单里，目前只检索检验项目（肝肾功能、血脂、血糖等）。",
    "体温": "体温不在化验单里，目前只检索检验项目。",
    "心率": "心率不在化验单里，目前只检索检验项目。",
}


def _suggest_names(query: str, names: list[str], limit: int = 8) -> list[str]:
    q = normalize_text(query)
    have = {normalize_text(n): n for n in names}
    if len(q) >= 2:
        grams = {q[i : i + 2] for i in range(len(q) - 1)}
        ranked: list[tuple[int, str]] = []
        for name in names:
            n = normalize_text(name)
            overlap = sum(1 for g in grams if g in n)
            if overlap:
                ranked.append((overlap, name))
        ranked.sort(key=lambda item: (-item[0], len(item[1])))
        if ranked:
            return [name for _, name in ranked[:limit]]
    preferred = [have[normalize_text(n)] for n in _PREFERRED_SUGGESTIONS if normalize_text(n) in have]
    return (preferred or names)[:limit]


def _latest_by_name(hits: list[LabHit], name: str) -> LabHit | None:
    matched = [h for h in hits if normalize_text(h.test_name) == normalize_text(name)]
    matched = _sort_hits(matched)
    return matched[0] if matched else None


def _overview_result(intent: QueryIntent, hits: list[LabHit]) -> LabQueryResult:
    dated = [h for h in hits if h.visit_date]
    if not dated:
        return LabQueryResult(intent=intent, message="有化验记录，但没有就诊日期，无法判断最近一次。")
    latest_day = max(h.visit_date for h in dated if h.visit_date)
    day_hits = [h for h in hits if h.visit_date == latest_day]
    # De-dupe by name, keep first (already mixed records that day)
    uniq: list[LabHit] = []
    seen: set[str] = set()
    for hit in day_hits:
        key = normalize_text(hit.test_name)
        if key in seen:
            continue
        seen.add(key)
        uniq.append(hit)
    abn = [h for h in uniq if h.status in _ABNORMAL]
    person = intent.person_name or uniq[0].person_name
    parts = [f"{person} 最近一次化验是 {latest_day.isoformat()}，共 {len(uniq)} 项"]
    if abn:
        parts.append(f"其中 {len(abn)} 项异常：")
        parts.append(
            "、".join(
                f"{h.test_name} {h.value}{h.unit or ''}（{STATUS_LABEL.get(h.status, h.status)}）" for h in abn[:10]
            )
        )
        parts.append("。")
    else:
        parts.append("，未标出明显异常。")
    if intent.inferred_person:
        parts.append(f"未指定人员，已按 {person} 查询。")
    hit = abn[0] if abn else uniq[0]
    return LabQueryResult(
        intent=intent,
        hit=hit,
        hits=uniq,
        analysis="".join(parts),
        ok=True,
        kind="overview",
    )


def _panel_result(intent: QueryIntent, hits: list[LabHit], panel: str) -> LabQueryResult:
    timed = _filter_by_time(hits, intent) or hits
    picked: list[LabHit] = []
    for name in PANELS[panel]:
        latest = _latest_by_name(timed, name)
        if latest:
            picked.append(latest)
    if not picked:
        return LabQueryResult(
            intent=intent,
            message=f"化验单里还没有「{panel}」相关项目。",
            suggestions=_suggest_names(panel, _unique_names(hits)),
        )
    abn = [h for h in picked if h.status in _ABNORMAL]
    person = intent.person_name or picked[0].person_name
    bits = [
        f"{h.test_name} {h.value}{h.unit or ''}（{STATUS_LABEL.get(h.status, h.status or '未知')}）" for h in picked
    ]
    analysis = f"{person} 的{panel}：" + "；".join(bits) + "。"
    if abn:
        analysis += f"其中 {len(abn)} 项异常，建议对照化验单咨询医生。"
    if intent.inferred_person:
        analysis += f"未指定人员，已按 {person} 查询。"
    return LabQueryResult(
        intent=intent,
        hit=picked[0],
        hits=picked,
        analysis=analysis,
        ok=True,
        kind="panel",
    )


def _pick_metric(query_metric: str, scored: list[tuple[int, LabHit]]) -> tuple[list[LabHit], int]:
    best = max(s for s, _ in scored)
    top = [h for s, h in scored if s == best]
    names = {h.test_name for h in top}
    if len(names) > 1:
        winner = min(names, key=lambda name: _name_tiebreak(query_metric, name))
        top = [h for h in top if h.test_name == winner]
    return _sort_hits(top), best


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

    remainder = _metric_remainder(text, intent.person_key)
    panel = find_panel(remainder)
    if not intent.metric and remainder:
        intent.metric = remainder

    if allow_llm and not intent.metric and not panel and remainder:
        llm_fn = llm_fn or _call_llm_intent
        llm_data = llm_fn(text)
        if llm_data:
            intent = merge_llm_intent(intent, llm_data)
            remainder = intent.metric or remainder

    person = resolve_person(persons, intent.person_key)
    if intent.person_key and person is None:
        return LabQueryResult(intent=intent, message=f"找不到人员「{intent.person_key}」。目前档案是 qian / tjh。")

    if person is None:
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
    catalog = _catalog(records, person)
    if not catalog:
        return LabQueryResult(
            intent=intent,
            message=f"{person.name} 目前没有结构化化验报告可查询（只有已 OCR 并解析出检验项目的化验单才能检索）。",
        )

    names = _unique_names(catalog)
    metric_query = remainder or intent.metric or ""

    vital_msg = _VITALS.get(normalize_text(metric_query))
    if vital_msg:
        return LabQueryResult(intent=intent, message=vital_msg, suggestions=_suggest_names(metric_query, names))

    if panel:
        intent.metric = panel
        return _panel_result(intent, catalog, panel)

    if not metric_query:
        return _overview_result(intent, catalog)

    scored = [(score_name(metric_query, h.test_name), h) for h in catalog]
    scored = [(s, h) for s, h in scored if s >= (100 if len(normalize_text(metric_query)) == 1 else MIN_SCORE)]
    if not scored:
        # Try alias-canonical as a second pass (HbA1c → 糖化血红蛋白).
        aliased = find_metric(metric_query)
        if aliased and aliased != metric_query:
            scored = [(score_name(aliased, h.test_name), h) for h in catalog]
            scored = [(s, h) for s, h in scored if s >= MIN_SCORE]
            if scored:
                metric_query = aliased
    if not scored:
        suggestions = _suggest_names(metric_query, names)
        if suggestions:
            hint = f"可以试试：{'、'.join(suggestions)}。"
        else:
            hint = f"{person.name} 的化验项目包括：{'、'.join(names[:8])}。"
        return LabQueryResult(
            intent=intent,
            message=f"在 {person.name} 的化验单里没有找到「{metric_query}」。{hint}",
            suggestions=suggestions or names[:8],
        )

    matched, _best = _pick_metric(metric_query, scored)
    timed = _filter_by_time(matched, intent)
    if intent.time_mode in {"on_date", "in_month"} and not timed:
        return LabQueryResult(
            intent=intent,
            message=f"找到了「{matched[0].test_name}」，但指定时间没有记录。最近一次是 {_fmt_hit(matched[0])}。",
            candidates=matched[:3],
            suggestions=[matched[0].test_name],
        )

    pool = timed or matched
    hit = pool[0]
    previous = pool[1] if len(pool) > 1 else None
    if previous is None:
        older = [
            h
            for h in matched
            if h.record_id != hit.record_id and (h.visit_date or date.min) < (hit.visit_date or date.min)
        ]
        previous = older[0] if older else None

    intent.metric = hit.test_name
    analysis = build_analysis(hit, previous, intent.inferred_person)
    return LabQueryResult(
        intent=intent,
        hit=hit,
        previous=previous,
        hits=[hit],
        analysis=analysis,
        ok=True,
        kind="metric",
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
        "kind": result.kind,
        "hits": [hit_dict(h) for h in result.hits if h is not None],
        "suggestions": result.suggestions,
    }
