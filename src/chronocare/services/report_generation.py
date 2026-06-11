"""Report generation orchestration service.

Handles: create record → aggregate data → build prompt → generate image → persist.
Uses Hermes CLI subprocess for image generation.
"""

from __future__ import annotations

import asyncio
import gzip
import json
import os
import time
from datetime import UTC, datetime
from pathlib import Path

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from chronocare.models.report_generation import ReportGeneration
from chronocare.services.report_data import aggregate_person_data

# Report storage directory
REPORTS_DIR = Path("data/reports")
# Hermes image generation script
HERMES_SCRIPT = Path(__file__).resolve().parent.parent.parent.parent / "scripts" / "hermes_image_generate.py"


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
) -> ReportGeneration:
    """Execute the full report generation pipeline.

    1. Load report record
    2. Aggregate person data
    3. Build prompt (baoyu-infographic style)
    4. Call Hermes CLI for image generation
    5. Save result + update record
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

        # Step 3: Generate image via Hermes CLI
        aspect = "portrait" if report.layout == "pc" else "square"
        image_url = await _hermes_image_generate(prompt, aspect)

        # Step 4: Download and save image locally
        local_path = await _download_image(image_url, report.id, report.layout)

        # Step 5: Persist
        elapsed = time.time() - start_time
        data_json = json.dumps(data, ensure_ascii=False, default=str)
        data_gzipped = gzip.compress(data_json.encode("utf-8"))

        report.status = "completed"
        report.image_path = local_path or image_url  # prefer local, fallback to CDN
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


async def _hermes_image_generate(prompt: str, aspect: str = "portrait", max_retries: int = 2) -> str:
    """Call Hermes CLI via subprocess to generate an image.

    Retries on timeout up to max_retries times.
    Returns the image URL or path string.
    Raises RuntimeError on failure.
    """
    if not HERMES_SCRIPT.exists():
        raise RuntimeError(f"Hermes script not found: {HERMES_SCRIPT}")

    last_error = None
    for attempt in range(max_retries + 1):
        try:
            proc = await asyncio.create_subprocess_exec(
                "python3",
                str(HERMES_SCRIPT),
                prompt,
                "--aspect", aspect,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                env={**os.environ, "PYTHONUNBUFFERED": "1"},
            )
            stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=180)

            if proc.returncode != 0:
                raise RuntimeError(f"Hermes script failed (rc={proc.returncode}): {stderr.decode()[:500]}")

            try:
                result = json.loads(stdout.decode().strip())
            except json.JSONDecodeError as exc:
                raise RuntimeError(
                    f"Invalid JSON from hermes script: {stdout.decode()[:500]}"
                ) from exc

            if "error" in result:
                error_msg = result["error"]
                # Check if it's a timeout error
                if "timed out" in error_msg.lower() and attempt < max_retries:
                    last_error = error_msg
                    continue  # retry
                raise RuntimeError(f"Image generation error: {error_msg}")

            url = result.get("url") or result.get("path") or result.get("image", "")
            if not url:
                raise RuntimeError(f"No image URL in result: {result}")

            return url

        except TimeoutError as e:
            last_error = f"Subprocess timeout (180s), attempt {attempt + 1}/{max_retries + 1}"
            if attempt < max_retries:
                continue  # retry
            raise RuntimeError(f"Image generation timed out after {max_retries + 1} attempts: {last_error}") from e

    raise RuntimeError(f"Image generation failed after {max_retries + 1} attempts: {last_error}")


async def _download_image(url: str, report_id: int, layout: str) -> str | None:
    """Download image from URL and save locally.

    Returns local path (relative to data/reports/) or None on failure.
    """
    import aiohttp

    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    filename = f"report_{report_id}_{layout}.png"
    local_path = REPORTS_DIR / filename

    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, timeout=aiohttp.ClientTimeout(total=30)) as resp:
                if resp.status == 200:
                    content = await resp.read()
                    local_path.write_bytes(content)
                    return f"data/reports/{filename}"
    except Exception:
        pass  # fallback to CDN URL
    return None


# ---------------------------------------------------------------------------
# Prompt building (baoyu-infographic morandi-journal + winding-roadmap)
# ---------------------------------------------------------------------------

# Color palette (locked from baoyu-infographic template)
_COLORS = """
COLOR PALETTE (use exactly these hex values):
- Background: #F5F0E6 (warm cream paper)
- Header/frame: #7BA3A8 (muted sage teal)
- Stable status: #8FA876 (soft olive green)
- Needs action: #D4956A (soft terracotta — NOT red)
- Highlight: #F5E6C8 (pale yellow callout)
- Text/lines: #4A4540 (charcoal brown — NOT pure black)
"""


def _build_prompt(data: dict, layout: str) -> str:
    """Build the image generation prompt.

    PC layout: winding-roadmap + morandi-journal (detailed A4 portrait)
    Mobile layout: simplified, large text, gift-like (square)
    """
    person = data["person"]
    summary = data["summary"]
    doctors = data["doctors"]
    diag = data["diagnosis_consistency"]
    bs = data["blood_sugar"]
    metrics = data["key_metrics"]

    name = person["name"]
    gender_str = "男" if person.get("gender") == "M" else "女"
    birth = person.get("birth_date") or "未知"
    dr = summary.get("date_range") or ["未知", "未知"]

    # Doctor summary
    doc_lines = []
    for doc_name, detail in doctors.get("details", {}).items():
        diag_str = "、".join(detail.get("diagnoses", [])[:5])
        doc_lines.append(f"- {doc_name}: {detail['pdf_count']}次就诊, 主要诊断: {diag_str}")
    doctor_text = "\n".join(doc_lines) if doc_lines else "暂无医生数据"

    # Diagnosis
    common = diag.get("common_across_doctors", [])
    common_text = "、".join(common) if common else "暂无"

    # Blood sugar
    bs_text = ""
    if bs.get("summary"):
        s = bs["summary"]
        bs_text = f"\n血糖记录: {s['count']}次, 平均{s['avg']}mmol/L, 范围{s['min']}-{s['max']}mmol/L"

    # Key metrics
    inr_text = ""
    if metrics.get("inr_values"):
        latest = metrics["inr_values"][-1]
        inr_text = f"\n最新INR: {latest['value']} ({latest['date']})"

    echo_text = ""
    if metrics.get("echo_findings"):
        items = [f"  - {e['text']}" for e in metrics["echo_findings"][:3]]
        echo_text = "\n心超关键发现:\n" + "\n".join(items)

    if layout == "pc":
        return f"""Generate a health report infographic.
Style: morandi-journal (hand-drawn doodle, warm Morandi tones).
Layout: winding-roadmap (S-curve path with milestones).

{_COLORS}

SUBJECT: {name}, {gender_str}, born {birth}
DATA PERIOD: {dr[0]} ~ {dr[1]}
TOTAL: {summary['visit_count']} visits, {summary['record_count']} medical records

DOCTORS:
{doctor_text}

CONSISTENT DIAGNOSIS: {common_text}

DIAGNOSIS BY DOCTOR:
{chr(10).join(f"- {d}: {', '.join(info.get('diagnoses', [])[:5])}" for d, info in diag.get('by_doctor', {}).items())}
{bs_text}{inr_text}{echo_text}

DESIGN REQUIREMENTS:
1. Winding roadmap with 5-7 milestone stations showing the patient's medical journey
2. Each milestone: date range + headline + 2-3 plain-language facts + status (稳定/持续管理/需进一步评估)
3. Bento cards for: doctor stats, diagnosis consistency, key lab values
4. Comparison table: initial vs current state, color-coded (olive green=stable, terracotta=needs action)
5. 4 sticky-note action items at the bottom with concrete next steps
6. CRITICAL: Use plain language with medical terms in parentheses. Example: "心脏的'小门'关得不够紧(二尖瓣关闭不全)"
7. CRITICAL: No red/orange-red. No emoji. No "不用太担心" or "请遵医嘱"
8. Chinese language throughout
9. Aspect: portrait 3:4 (A4 print-friendly)
"""
    else:
        # Mobile: simplified, large text, gift-like
        return f"""Generate a health report card for elderly person. Style: morandi-journal, warm and gift-like.

{_COLORS}

SUBJECT: {name}, {gender_str}
PERIOD: {dr[0]} ~ {dr[1]}

KEY FINDINGS:
- Total visits: {summary['visit_count']} times
- Main diagnoses: {common_text}
{bs_text}{inr_text}

DESIGN REQUIREMENTS:
1. Large text (>24px equivalent), high contrast, generous whitespace
2. Single column, 3-5 key information blocks maximum
3. Color: olive green (#8FA876) = stable, terracotta (#D4956A) = needs action
4. Include a small family/health icon motif for emotional warmth
5. Plain language only — elderly reader must understand without medical background
6. No red, no emoji, no alarming language
7. Chinese language
8. Square 1:1 format (WeChat sharing friendly)
"""
