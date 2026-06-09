"""Report generation orchestration service.

Handles: create record → aggregate data → build prompt → generate image → persist.
"""

from __future__ import annotations

import gzip
import json
import time
from datetime import UTC, datetime
from pathlib import Path

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from chronocare.models.report_generation import ReportGeneration
from chronocare.services.report_data import aggregate_person_data

# Report storage directory
REPORTS_DIR = Path("data/reports")


async def create_report_record(
    db: AsyncSession, person_id: int, layout: str
) -> ReportGeneration:
    """Create a pending report generation record."""
    report = ReportGeneration(
        person_id=person_id,
        layout=layout,
        status="pending",
    )
    db.add(report)
    await db.commit()
    await db.refresh(report)
    return report


async def get_report(db: AsyncSession, report_id: int) -> ReportGeneration | None:
    """Get a single report generation by ID."""
    return await db.scalar(
        select(ReportGeneration).where(ReportGeneration.id == report_id)
    )


async def list_person_reports(
    db: AsyncSession, person_id: int, limit: int = 20
) -> list[ReportGeneration]:
    """List reports for a person, newest first."""
    result = await db.execute(
        select(ReportGeneration)
        .where(ReportGeneration.person_id == person_id)
        .order_by(ReportGeneration.created_at.desc())
        .limit(limit)
    )
    return list(result.scalars().all())


async def generate_report(
    db: AsyncSession,
    report_id: int,
    image_generate_fn,  # injected: callable(prompt, aspect_ratio) -> url/path
) -> ReportGeneration:
    """Execute the full report generation pipeline.

    1. Load report record
    2. Aggregate person data
    3. Build prompt
    4. Call image_generate
    5. Save image + update record

    Args:
        db: async session
        report_id: the ReportGeneration record ID
        image_generate_fn: callable(prompt: str, aspect_ratio: str) -> str
    """
    report = await get_report(db, report_id)
    if not report:
        raise ValueError(f"Report {report_id} not found")

    # Mark generating
    report.status = "generating"
    await db.commit()

    start_time = time.time()

    try:
        # Step 1: Aggregate data
        data = await aggregate_person_data(db, report.person_id)

        # Step 2: Build prompt
        prompt = _build_prompt(data, report.layout)

        # Step 3: Generate image
        aspect_ratio = "portrait" if report.layout == "pc" else "square"
        image_result = image_generate_fn(prompt, aspect_ratio=aspect_ratio)

        # image_result can be a URL string or a dict with 'image'/'url' key
        if isinstance(image_result, dict):
            image_path = image_result.get("image") or image_result.get("url", "")
        else:
            image_path = str(image_result)

        # Step 4: Persist
        elapsed = time.time() - start_time
        data_json = json.dumps(data, ensure_ascii=False, default=str)
        data_gzipped = gzip.compress(data_json.encode("utf-8"))

        report.status = "completed"
        report.image_path = image_path
        report.prompt_snapshot = prompt
        report.data_snapshot = data_gzipped
        report.generation_seconds = round(elapsed, 2)
        report.completed_at = datetime.now(UTC)
        await db.commit()
        await db.refresh(report)

    except Exception as e:
        report.status = "failed"
        report.error_message = str(e)[:2000]
        report.completed_at = datetime.now(UTC)
        await db.commit()
        raise

    return report


def _build_prompt(data: dict, layout: str) -> str:
    """Build the image generation prompt based on data and layout.

    PC layout: morandi-journal + winding-roadmap style (detailed A4)
    Mobile layout: simplified, large text, gift-like
    """
    person = data["person"]
    summary = data["summary"]
    doctors = data["doctors"]
    diag = data["diagnosis_consistency"]
    bs = data["blood_sugar"]
    metrics = data["key_metrics"]

    # Person basic info
    name = person["name"]
    gender_str = "男" if person.get("gender") == "M" else "女"
    birth = person.get("birth_date", "未知")
    date_range = data["summary"].get("date_range") or ["未知", "未知"]

    # Doctor summary
    doctor_lines = []
    for doc_name, detail in doctors.get("details", {}).items():
        diag_str = "、".join(detail.get("diagnoses", [])[:5])
        doctor_lines.append(f"- {doc_name}: {detail['pdf_count']}次就诊, 主要诊断: {diag_str}")
    doctor_text = "\n".join(doctor_lines) if doctor_lines else "暂无医生数据"

    # Diagnosis summary
    common = diag.get("common_across_doctors", [])
    common_text = "、".join(common) if common else "暂无"

    # Blood sugar summary
    bs_text = ""
    if bs.get("summary"):
        s = bs["summary"]
        bs_text = f"\n血糖记录: {s['count']}次, 平均{s['avg']}mmol/L, 范围{s['min']}-{s['max']}mmol/L"

    # Key metrics
    inr_text = ""
    if metrics.get("inr_values"):
        latest_inr = metrics["inr_values"][-1]
        inr_text = f"\n最新INR: {latest_inr['value']} ({latest_inr['date']})"

    echo_text = ""
    if metrics.get("echo_findings"):
        echo_items = [f"  - {e['text']}" for e in metrics["echo_findings"][:3]]
        echo_text = "\n心超关键发现:\n" + "\n".join(echo_items)

    if layout == "pc":
        return f"""Generate a health report infographic in morandi-journal + winding-roadmap style.

Subject: {name}, {gender_str}, born {birth}
Data period: {date_range[0]} ~ {date_range[1]}
Total visits: {summary['visit_count']} | Medical records: {summary['record_count']}

VISITING DOCTORS:
{doctor_text}

CONSISTENT DIAGNOSIS (all doctors agree): {common_text}

DIAGNOSIS BY DOCTOR:
{chr(10).join(f"- {d}: {', '.join(info.get('diagnoses', [])[:5])}" for d, info in diag.get('by_doctor', {}).items())}
{bs_text}{inr_text}{echo_text}

Design requirements:
- Winding roadmap timeline showing the patient's medical journey with 4-6 key stations
- Bento grid cards for doctor statistics, diagnosis consistency, key metrics
- Color coding: olive green = stable, terracotta orange = needs treatment
- Tone: medically accurate + warm (not alarming, not downplaying)
- Chinese language, medical terms with parenthetical explanations for elderly readers
- A4 portrait (3:4), print-friendly
"""
    else:
        # Mobile: simplified, large text, fewer data points
        return f"""Generate a health report card for elderly person, mobile-friendly.

Subject: {name}, {gender_str}
Period: {date_range[0]} ~ {date_range[1]}

KEY FINDINGS:
- Visits: {summary['visit_count']} times
- Main diagnoses: {common_text}
{bs_text}{inr_text}

Design requirements:
- Large text (>24px equivalent), high contrast
- Single column vertical layout, card stacking
- Only 3-5 key information blocks maximum
- Color coding: olive green = stable, terracotta orange = needs treatment
- Warm, gift-like feel suitable for WeChat sharing
- Square (1:1) format
- Chinese language, simple wording elderly can understand
- Include a small family/health icon motif for emotional warmth
"""
