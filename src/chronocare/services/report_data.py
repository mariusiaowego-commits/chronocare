"""Report data aggregation service.

Refactored from scripts/analyze_tjh_history.py — works for any person_id.
Aggregates visits, medical_records, blood_sugar into structured JSON for report generation.
"""

from __future__ import annotations

import re
from collections import Counter, defaultdict
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from chronocare.models.blood_sugar import BloodSugarRecord
from chronocare.models.medical_record import MedicalRecord
from chronocare.models.person import Person
from chronocare.models.visit import Visit

# ---------------------------------------------------------------------------
# Pure helper functions (directly reusable from the original script)
# ---------------------------------------------------------------------------

def parse_diagnosis(diag_str: str | None) -> list[str]:
    """Parse '1.诊断A 2.诊断B' format into list."""
    if not diag_str:
        return []
    diag_str = diag_str.replace("西医诊断:", "").replace("中医诊断:", "").strip()
    diag_str = diag_str.replace("西医诊断：", "").replace("中医诊断：", "").strip()
    parts = re.split(r"\d+\.", diag_str)
    return [p.strip() for p in parts if p.strip() and p.strip() not in ("西医诊断：", "西医诊断:")]


def normalize_diag(s: str) -> str:
    """Normalize diagnosis variants to canonical form."""
    s = s.strip()
    # Remove parentheses variants
    s = s.replace("(慢性)", "").replace("（慢性）", "")
    s = s.replace("(瓣)", "瓣").replace("（瓣）", "瓣")
    # Normalize insomnia variants
    if "失眠" in s or "睡眠" in s:
        return "失眠"
    # Normalize mitral valve variants
    if "二尖瓣" in s or "二尖" in s:
        if "关闭不全" in s or "反流" in s:
            return "二尖瓣关闭不全"
    # Normalize atrial fibrillation
    if "心房颤动" in s or "房颤" in s:
        return "心房颤动"
    # Normalize hypertension
    if "高血压" in s:
        return "高血压"
    return s


def extract_doctor(text: str | None, known_doctors: set[str] | None = None) -> str | None:
    """Extract doctor name from OCR text signature.

    Strategy: doctor name is a 2-3 char Chinese name near page marker '1/N'.
    Round 1 (known_doctors=None): blacklist filtering.
    Round 2 (known_doctors provided): prioritize known doctors first.
    """
    if not text:
        return None
    parts = re.split(r"\b\d+/\d+\b", text)
    sig_page = None
    for p in parts:
        if p.strip():
            sig_page = p
            break
    if not sig_page:
        return None

    after_xz = re.split(r"随访[,，]", sig_page)
    candidate_text = after_xz[-1] if len(after_xz) > 1 else sig_page

    # Medical/common term blacklist (no patient-specific names)
    blacklist = {
        "随访", "复查", "继续", "治疗", "方案", "定期", "相关", "指标", "如有", "不适",
        "及时", "就诊", "完善", "疾病", "药物", "宣教", "密切", "注意", "休息", "保暖",
        "规律", "作息", "饮食", "避免", "劳累", "情绪", "激动", "建议", "心外", "高血压",
        "心房", "颤动", "二尖", "关闭", "不全", "慢性", "失眠", "眼痒", "病人", "主诉",
        "病史", "体格", "检查", "诊断", "处理", "科室", "医院", "上海市", "医学中心",
        "门诊", "处方", "检验", "动态", "观察", "全程", "基础", "心动", "次数", "心室",
        "平均", "单个", "未见", "缺血", "型", "左眼", "结膜", "炎", "结石", "造影",
        "出凝血", "一般可", "壁增厚", "临检", "带药", "静注", "速尿", "每日", "每晚",
        "每次", "华法令", "侧位", "医学", "中心", "反流", "脱垂", "中重度",
        "增大", "室壁", "增厚", "室早", "心动过速", "心动过缓", "心律", "绝对", "不齐",
        "律不齐", "律齐", "口服", "滴眼", "测定", "出凝",
        "呼出气", "支气管", "哮喘", "顺尔宁", "爬楼梯", "胸闷", "气促",
        "动脉", "瓣", "测出", "黄绿", "绿", "吸入", "气雾",
        "喷雾", "信必可", "都保", "粉吸入", "替卡松", "沙美特罗", "沙丁胺醇", "异丙托",
        "溴铵", "希刻劳", "头孢", "克洛", "分散片", "颗粒", "阿莫", "西林", "克拉",
        "维酸", "胸膜炎", "胸膜", "肺炎", "慢支", "肺心病", "肺气肿", "老慢支", "五分法",
        "分法",
    }

    cands = re.findall(
        r"(?<![\u4e00-\u9fff])([\u4e00-\u9fff]{2,3})(?![\u4e00-\u9fff])",
        candidate_text,
    )

    # Priority: known doctors first
    if known_doctors:
        for x in reversed(cands):
            if x in known_doctors:
                return x

    # Fallback: blacklist filtering
    for x in reversed(cands):
        if x in blacklist:
            continue
        if re.search(r"科|院|部|室|门|诊|病|医|师|士|生|号|路|区", x):
            continue
        return x
    return None


# ---------------------------------------------------------------------------
# Metric extraction helpers
# ---------------------------------------------------------------------------

def extract_inr_values(records: list[dict]) -> list[dict[str, str]]:
    """Extract INR values from medical records OCR text."""
    results = []
    for rec in records:
        ocr = rec.get("ocr_text") or ""
        m = re.search(r"国际标准化比值[:：]\s*([\d.]+)", ocr)
        if m:
            results.append({"date": rec.get("visit_date", ""), "value": m.group(1)})
    return results


def extract_echo_findings(records: list[dict]) -> list[dict[str, str]]:
    """Extract echocardiogram key findings from OCR text."""
    findings = []
    keywords = ["二尖瓣", "左室", "射血", "左房", "EF"]
    for rec in records:
        ocr = rec.get("ocr_text") or ""
        for kw in keywords:
            m = re.search(rf"{kw}[^。\n]{{0,40}}[。\n]", ocr)
            if m:
                findings.append({
                    "date": rec.get("visit_date", ""),
                    "keyword": kw,
                    "text": m.group(0).strip()[:80],
                })
                break
    return findings


# ---------------------------------------------------------------------------
# Main aggregation function
# ---------------------------------------------------------------------------

async def aggregate_person_data(db: AsyncSession, person_id: int) -> dict[str, Any]:
    """Aggregate all health data for a person into structured JSON.

    Returns dict with keys:
        person: basic info
        summary: data scale
        doctors: doctor frequency / diagnoses / visit dates
        diagnosis_consistency: common diagnoses across doctors
        blood_sugar: blood sugar statistics
        key_metrics: INR / echo findings
    """
    # --- Fetch person ---
    person = await db.scalar(select(Person).where(Person.id == person_id))
    if not person:
        raise ValueError(f"Person {person_id} not found")

    # --- Fetch visits ---
    result = await db.execute(
        select(Visit).where(Visit.person_id == person_id).order_by(Visit.visit_date)
    )
    visits_raw = result.scalars().all()
    visits = [
        {
            "id": v.id,
            "visit_date": v.visit_date,
            "hospital": v.hospital,
            "department": v.department,
            "doctor": v.doctor,
            "chief_complaint": v.chief_complaint,
            "diagnosis": v.diagnosis,
            "prescription": v.prescription,
        }
        for v in visits_raw
    ]

    # --- Fetch medical records ---
    result = await db.execute(
        select(MedicalRecord)
        .where(MedicalRecord.person_id == person_id)
        .order_by(MedicalRecord.visit_date)
    )
    mrs_raw = result.scalars().all()
    mrs = [
        {
            "id": m.id,
            "visit_date": m.visit_date,
            "hospital": m.hospital,
            "department": m.department,
            "doctor": m.doctor,
            "ocr_text": m.ocr_text,
            "structured_data": m.structured_data,
        }
        for m in mrs_raw
    ]

    # --- Fetch blood sugar ---
    result = await db.execute(
        select(BloodSugarRecord)
        .where(BloodSugarRecord.person_id == person_id)
        .order_by(BloodSugarRecord.measured_at)
    )
    bs_raw = result.scalars().all()
    blood_sugar_records = [
        {
            "id": b.id,
            "measured_at": b.measured_at.isoformat() if b.measured_at else None,
            "value": b.value,
            "meal_context": b.meal_context,
            "notes": b.notes,
        }
        for b in bs_raw
    ]

    # --- Pair visits + medical records by (date, hospital) ---
    mr_by_key: dict[tuple, list[dict]] = defaultdict(list)
    for m in mrs:
        if m["visit_date"]:
            mr_by_key[(m["visit_date"], m["hospital"])].append(m)

    # --- Doctor extraction (two-round strategy) ---
    round1 = []
    for v in visits:
        key = (v["visit_date"], v["hospital"])
        for m in mr_by_key.get(key, []):
            d = extract_doctor(m.get("ocr_text"))
            round1.append((v["visit_date"], v["hospital"], m.get("department"), v["diagnosis"], d))

    high_conf = Counter(d for _, _, _, _, d in round1 if d)
    known_doctors: set[str] = set()
    for name, cnt in high_conf.most_common():
        if cnt >= 2:
            known_doctors.add(name)
    single_hits = [n for n, c in high_conf.most_common() if c == 1]

    # Round 2: use known_doctors for better recall
    doctor_counter: Counter[str] = Counter()
    doctor_patients: dict[str, set] = defaultdict(set)
    doctor_diagnoses: dict[str, set] = defaultdict(set)
    no_doctor_pdfs = 0

    for v in visits:
        key = (v["visit_date"], v["hospital"])
        docs_this_visit = []
        for m in mr_by_key.get(key, []):
            d = extract_doctor(m.get("ocr_text"), known_doctors=known_doctors)
            if d:
                docs_this_visit.append(d)
                doctor_counter[d] += 1
                for x in parse_diagnosis(v["diagnosis"]):
                    doctor_diagnoses[d].add(normalize_diag(x))
            else:
                no_doctor_pdfs += 1
        for d in docs_this_visit:
            doctor_patients[d].add(v["visit_date"])

    # --- Diagnosis consistency ---
    all_diags: set[str] = set()
    for v in visits:
        for d in parse_diagnosis(v["diagnosis"]):
            all_diags.add(normalize_diag(d))

    all_doc_diags_norm: dict[str, set[str]] = {}
    for d in doctor_diagnoses:
        all_doc_diags_norm[d] = doctor_diagnoses[d]

    common_diags = (
        set.intersection(*all_doc_diags_norm.values()) if all_doc_diags_norm else set()
    )

    doctor_diffs = {}
    for d, diags in all_doc_diags_norm.items():
        others = (
            set.union(*[s for k, s in all_doc_diags_norm.items() if k != d])
            if len(all_doc_diags_norm) > 1
            else set()
        )
        doctor_diffs[d] = {
            "only_this": sorted(diags - others),
            "only_others": sorted(others - diags),
        }

    # --- Key metrics ---
    inr_values = extract_inr_values(mrs)
    echo_findings = extract_echo_findings(mrs)

    # --- Blood sugar summary ---
    bs_summary = {}
    if blood_sugar_records:
        values = [r["value"] for r in blood_sugar_records if r["value"] is not None]
        if values:
            bs_summary = {
                "count": len(values),
                "avg": round(sum(values) / len(values), 1),
                "min": min(values),
                "max": max(values),
                "latest": blood_sugar_records[-1],
            }

    # --- Build result ---
    date_range = []
    if visits:
        date_range = [visits[0]["visit_date"], visits[-1]["visit_date"]]

    return {
        "person": {
            "id": person.id,
            "name": person.name,
            "gender": person.gender,
            "birth_date": person.birth_date.isoformat() if person.birth_date else None,
        },
        "summary": {
            "visit_count": len(visits),
            "record_count": len(mrs),
            "blood_sugar_count": len(blood_sugar_records),
            "date_range": date_range,
        },
        "doctors": {
            "high_frequency": sorted(known_doctors),
            "single_hit_candidates": single_hits,
            "no_doctor_pdfs": no_doctor_pdfs,
            "details": {
                name: {
                    "pdf_count": doctor_counter[name],
                    "visit_days": len(doctor_patients[name]),
                    "visit_dates": sorted(doctor_patients[name]),
                    "diagnoses": sorted(doctor_diagnoses.get(name, set())),
                }
                for name in sorted(doctor_counter.keys(), key=lambda x: -doctor_counter[x])
            },
        },
        "diagnosis_consistency": {
            "all_diagnoses": sorted(all_diags),
            "common_across_doctors": sorted(common_diags),
            "by_doctor": {
                d: {
                    "diagnoses": sorted(all_doc_diags_norm.get(d, set())),
                    "diff": doctor_diffs.get(d, {}),
                }
                for d in sorted(all_doc_diags_norm.keys())
            },
        },
        "blood_sugar": {
            "records": blood_sugar_records,
            "summary": bs_summary,
        },
        "key_metrics": {
            "inr_values": inr_values,
            "echo_findings": echo_findings,
        },
        "_visits": visits,  # raw visit data for prompt milestone building
    }
