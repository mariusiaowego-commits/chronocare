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
# v3 detailed version — structured milestones, bento cards, comparison table
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

# Elderly-friendly language translation table
_LANG_GUIDE = """
LANGUAGE TRANSLATION TABLE (use left column in the infographic, medical term in parentheses):
- 心房颤动 → 心跳不太规律(房颤)
- 二尖瓣关闭不全 → 心脏的"小门"关得不够紧(二尖瓣关闭不全)
- 高血压 → 血压偏高
- (慢性)失眠 → 睡眠不太好
- INR → 血的稀稠度(INR)
- 华法林/华法令 → 抗凝药(华法林),预防中风
- 诺欣妥 → 降压护心药(诺欣妥)
- 络活喜 → 降压药(络活喜)
- 思诺思 → 帮助睡觉的药(思诺思)
- 心外科 → 心外科(做心脏手术的科)
- 胸膜炎 → 胸膜有点发炎(胸膜炎)
- 咳嗽变异性哮喘 → 咳嗽型哮喘
- 冠脉CT造影 → 心脏血管CT
- 超声心动图 → 心脏B超
- 动态心电图 → 24小时心电图
- 三尖瓣反流 → 另一个"小门"也漏了一点(三尖瓣反流)
- 射血分数 → 心脏泵血能力(射血分数)
"""

# Tone guidelines
_TONE_GUIDE = """
CRITICAL — Tone Guidelines (ACCURATE + GENTLE, NOT Alarmist, NOT Downplaying)
This infographic is for an elderly patient and their family. The tone must be MEDICALLY ACCURATE BUT NOT ALARMING.

✅ DO say (accurate, plain, professional):
- "中风风险" — medically necessary
- "出血风险" — important for INR context
- "需手术评估" — clear, professional
- "需调整剂量" — clear action
- "需进一步治疗" — clear and accurate
- "病情加重" — accurate when applicable

⚠️ SOFTEN from harsh clinical terms BUT DON'T remove:
- "二尖瓣关闭不全" → "心脏的'小门'关得不够紧(二尖瓣关闭不全)"
- "出血风险升高" → "偏高,出血风险↑"
- Keep medical terms visible in parentheses

❌ AVOID (too soft, misleading):
- Don't replace "出血风险" with just "数字高了一些"
- Don't replace "需手术评估" with just "可以慢慢聊不着急"
- Don't replace "失眠加重" with just "需要多关注"

✅ END each section with CALM, PROFESSIONAL phrases:
- "医生在持续管理"
- "需定期复诊"
- "需要进一步评估"
- NOT "不用太担心" (dismissive)
- NOT "请遵医嘱" (too generic)
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

    # Calculate age
    age_text = ""
    if person.get("birth_date"):
        try:
            from datetime import date
            b = date.fromisoformat(person["birth_date"])
            today = date.today()
            age = today.year - b.year - ((today.month, today.day) < (b.month, b.day))
            age_text = f" {age}岁"
        except Exception:
            pass

    # --- Doctor summary for bento card ---
    doc_lines = []
    doc_bar_data = []
    for doc_name, detail in doctors.get("details", {}).items():
        cnt = detail["pdf_count"]
        diag_str = "、".join(detail.get("diagnoses", [])[:3])
        doc_lines.append(f"  - {doc_name}: {cnt}次就诊, 主要诊断: {diag_str}")
        doc_bar_data.append(f"  - {doc_name} {cnt}次")
    doctor_text = "\n".join(doc_lines) if doc_lines else "暂无医生数据"
    doctor_bar_text = "\n".join(doc_bar_data) if doc_bar_data else "暂无"

    # Note about post-2025-04 doctor extraction limitation
    no_doc_note = ""
    if doctors.get("no_doctor_pdfs", 0) > 0:
        no_doc_note = f"\n注意: {doctors['no_doctor_pdfs']}份病历因医院改为电子签名(图片格式)无法识别医生"

    # --- Diagnosis consistency ---
    common = diag.get("common_across_doctors", [])
    common_text = "、".join(common) if common else "暂无"

    # By-doctor diagnosis differences
    by_doc_lines = []
    for d, info in diag.get("by_doctor", {}).items():
        diags = ", ".join(info.get("diagnoses", [])[:5])
        by_doc_lines.append(f"  - {d}: {diags}")
    by_doc_text = "\n".join(by_doc_lines) if by_doc_lines else "暂无"

    # Unique diagnoses per doctor
    unique_lines = []
    for d, info in diag.get("by_doctor", {}).items():
        diff = info.get("diff", {})
        only_this = diff.get("only_this", [])
        if only_this:
            unique_lines.append(f"  - {d}: 独有诊断 {', '.join(only_this)}")
    unique_text = "\n".join(unique_lines) if unique_lines else ""

    # --- Blood sugar ---
    bs_text = ""
    if bs.get("summary"):
        s = bs["summary"]
        bs_text = f"\n血糖记录: {s['count']}次, 平均{s['avg']}mmol/L, 范围{s['min']}-{s['max']}mmol/L"

    # --- Key metrics ---
    inr_text = ""
    inr_detail_text = ""
    if metrics.get("inr_values"):
        vals = metrics["inr_values"]
        latest = vals[-1]
        inr_text = f"\n最新INR: {latest['value']} ({latest['date']})"
        # INR sparkline data
        inr_lines = []
        for v in vals:
            val = float(v["value"])
            status = "达标" if 1.5 <= val <= 2.0 else ("超标,出血风险↑" if val > 2.0 else "偏低,血栓风险↑")
            inr_lines.append(f"  - {v['date']}: {v['value']} ({status})")
        inr_detail_text = "\nINR变化趋势:\n" + "\n".join(inr_lines)

    echo_text = ""
    if metrics.get("echo_findings"):
        items = [f"  - {e['text']}" for e in metrics["echo_findings"][:5]]
        echo_text = "\n心脏B超关键发现:\n" + "\n".join(items)

    # --- Visit timeline for roadmap milestones ---
    visit_dates = []
    for v in data.get("_visits", []):
        if v.get("visit_date"):
            visit_dates.append(v["visit_date"])

    # --- Build milestone phases from visit dates ---
    milestones_text = ""
    if visit_dates:
        first = visit_dates[0]
        last = visit_dates[-1]
        mid_idx = len(visit_dates) // 3
        mid = visit_dates[mid_idx] if mid_idx < len(visit_dates) else first
        milestones_text = f"""
ROADMAP MILESTONES (6 stations along S-curve):
Station ① — First visit ({first}): Initial consultation, diagnosis established
Station ② — Treatment adjustment ({first} ~ {mid}): Medication optimization
Station ③ — Stable follow-up ({mid} ~ {visit_dates[-1] if len(visit_dates) > mid_idx + 1 else last}): Ongoing management
Station ④ — Comprehensive review: Key tests and reassessment
Station ⑤ — Long-term maintenance: Continuous monitoring
Station ⑥ — Current status ({last}): Latest findings and next steps"""

    # Doctor count text for mobile prompt
    doctor_count_text = ""
    if doctors.get("details"):
        doc_count = len(doctors["details"])
        doctor_count_text = f'- "见过 {doc_count} 位医生"'

    if layout == "pc":
        return f"""Create a professional infographic following these specifications:

## Image Specifications
- Type: Infographic (single-page family health archive)
- Layout: winding-roadmap (S-curved path with 6 milestones)
- Style: morandi-journal (hand-drawn doodle, warm Morandi tones)
- Aspect Ratio: 3:4 (portrait, A4 print-friendly)
- Language: Chinese (Simplified)

{_COLORS}
{_TONE_GUIDE}
{_LANG_GUIDE}

## Content (Chinese — Plain, Accurate, Professional)

### 顶部标题区
- 主标题: "{name}的健康记录" (large, hand-lettered calligraphy, muted teal)
- 副标题: "{dr[0]} ~ {dr[1]}"
- 患者信息: "{name} {gender_str}{age_text}"
- 概览数字(柔和暖橘色圆角标签):
  - "看了 {summary['visit_count']} 次病"
  - "有 {summary['record_count']} 份病历"
  - "见过 {len(doctors.get('details', {}))} 位医生"
{bs_text}

### 路线图主体(winding-roadmap, 6个站点沿S曲线分布)
{milestones_text}

Each milestone should include:
- Date range + headline
- 2-3 plain-language facts from the data below
- Status indicator: 稳定(olive green) / 持续管理(sage teal) / 需进一步评估(terracotta)
- Small hand-drawn icon

DATA FOR MILESTONES:
DOCTORS:
{doctor_text}
{no_doc_note}

CONSISTENT DIAGNOSIS: {common_text}

DIAGNOSIS BY DOCTOR:
{by_doc_text}

{f"UNIQUE DIAGNOSES:{chr(10)}{unique_text}" if unique_text else ""}
{bs_text}{inr_text}{echo_text}

### 左侧bento卡片区

卡片A: "最常看的医生"
- 横向条形图(手绘风):
{doctor_bar_text}

卡片B: "医生诊断的一致性"
- 大圆圈: "{len(common)}项共识诊断"
  - {common_text}
- 周围小气泡: 各医生独有诊断
{unique_text if unique_text else "  - 所有医生诊断基本一致"}

### 右侧bento卡片区

卡片C: "血的稀稠度变化(INR)"
- 标题: "血的稀稠度(INR)"
- 副标: "目标 1.5 到 2.0"
- 简注: "华法林抗凝治疗需监测INR,偏高增加出血风险,偏低增加血栓风险"
{inr_detail_text if inr_detail_text else "- 暂无INR数据"}

卡片D: "当前病情评估"
- 两栏对比表: 初诊 vs 现在
- 每行用色块区分: olive green=稳定, terracotta=需进一步治疗
- 行项来自诊断列表和指标变化

### 底部 — 需要进一步治疗的事项(4个手绘便签)
基于诊断数据和指标变化,生成2-4个行动便签:
- 每个便签包含: 简短标题 + 当前状态 + 下一步建议
- 用陶土橘标签标注类别(需评估/需治疗/需调药/新发)
- 语气: 专业平和,既不吓人也不淡化

### 角落装饰
- 左上角: 小药瓶 + 听诊器(手绘)
- 右上角: 小爱心 + 小星
- 左下角: 日期 "{dr[1]}"
- 右下角: 小印 "家庭健康档案"
- 几条washi tape装饰条(暖色斜纹)

### 底部小字(术语简注)
- 房颤 = 心跳不太规律,需长期抗凝预防中风
- 二尖瓣 = 心脏4个"小门"之一,关不紧血会倒漏
- INR = 血的稀稠度,华法林疗效监测指标

CRITICAL TONE TARGET: Calm, professional, medically accurate. Like a kind family doctor explaining things to an elderly patient — honest about what needs treatment, but not dramatic. AVOID both scary clinical tone AND dismissive "everything's fine" tone. Find the middle ground: accurate + gentle.
"""
    else:
        # Mobile: simplified, large text, gift-like
        return f"""Generate a health report card for elderly person.

## Image Specifications
- Type: Health report card (gift-like, for WeChat sharing)
- Style: morandi-journal (warm, hand-drawn feel)
- Aspect Ratio: 1:1 (square, WeChat-friendly)
- Language: Chinese (Simplified)

{_COLORS}
{_TONE_GUIDE}

## Content — LARGE TEXT, 3-5 blocks maximum

### 标题区
- 主标题: "{name}的健康报告" (大字,手写风,柔和青绿色)
- 副标题: "{dr[0]} ~ {dr[1]}"
- 患者: "{name} {gender_str}{age_text}"

### 核心数字(大号,暖橘色标签)
- "看了 {summary['visit_count']} 次病"
- "有 {summary['record_count']} 份病历"
{doctor_count_text}
{bs_text}

### 诊断概要(简明列表)
- 共识诊断: {common_text}
- 用色区分: olive green=稳定, terracotta=需关注

### 关键指标
{inr_text if inr_text else "- 暂无特殊指标"}
{echo_text if echo_text else ""}

### 医生建议(2-3条大字便签)
基于数据生成简短的行动建议:
- 每条一行,大字清晰
- 语气温和但准确

DESIGN REQUIREMENTS:
1. Large text (main text > 24px equivalent), high contrast, generous whitespace
2. Single column, 3-5 key information blocks maximum
3. Color: olive green (#8FA876) = stable, terracotta (#D4956A) = needs action
4. Include small hand-drawn health icons for warmth
5. Plain language — elderly reader must understand without medical background
6. No red, no emoji, no alarming language
7. Chinese language throughout
8. Square 1:1 format (WeChat sharing friendly)
"""
