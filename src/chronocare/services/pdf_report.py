"""PDF report generation service."""

from datetime import datetime, timedelta
from pathlib import Path

from jinja2 import Environment, FileSystemLoader
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from chronocare.models.person import Person
from chronocare.models.blood_sugar import BloodSugarRecord
from chronocare.models.cardiac import BloodPressureRecord
from chronocare.models.medication import MedicationPlan, MedicationLog
from chronocare.models.visit import Visit
from chronocare.services.health_profile import get_health_overview
from chronocare.services.trend_alert import get_all_alerts
from chronocare.services.bs_variability import analyze_blood_sugar_variability


# Templates directory
TEMPLATES_DIR = Path(__file__).parent.parent / "templates" / "pdf"


async def generate_weekly_report(
    person_id: int,
    db: AsyncSession,
) -> bytes:
    """Generate weekly health report as PDF."""
    # Get person info
    person_stmt = select(Person).where(Person.id == person_id)
    person_result = await db.execute(person_stmt)
    person = person_result.scalar_one_or_none()
    
    if not person:
        raise ValueError("Person not found")
    
    # Get health overview
    overview = await get_health_overview(person_id, db)
    
    # Get trend alerts
    trends = await get_all_alerts(person_id, db)
    
    # Get blood sugar variability
    bs_variability = await analyze_blood_sugar_variability(person_id, days=7, db=db)
    
    # Get recent records
    week_ago = datetime.now() - timedelta(days=7)
    
    # Blood sugar records
    bs_stmt = (
        select(BloodSugarRecord)
        .where(BloodSugarRecord.person_id == person_id)
        .where(BloodSugarRecord.recorded_at >= week_ago)
        .order_by(BloodSugarRecord.recorded_at.desc())
    )
    bs_result = await db.execute(bs_stmt)
    bs_records = bs_result.scalars().all()
    
    # Blood pressure records
    bp_stmt = (
        select(BloodPressureRecord)
        .where(BloodPressureRecord.person_id == person_id)
        .where(BloodPressureRecord.recorded_at >= week_ago)
        .order_by(BloodPressureRecord.recorded_at.desc())
    )
    bp_result = await db.execute(bp_stmt)
    bp_records = bp_result.scalars().all()
    
    # Medication logs
    med_stmt = (
        select(MedicationLog)
        .where(MedicationLog.person_id == person_id)
        .where(MedicationLog.taken_at >= week_ago)
        .order_by(MedicationLog.taken_at.desc())
    )
    med_result = await db.execute(med_stmt)
    med_records = med_result.scalars().all()
    
    # Clinic visits
    visit_stmt = (
        select(Visit)
        .where(Visit.person_id == person_id)
        .where(Visit.visit_date >= week_ago.date())
        .order_by(Visit.visit_date.desc())
    )
    visit_result = await db.execute(visit_stmt)
    visit_records = visit_result.scalars().all()
    
    # Prepare template context
    context = {
        "person": person,
        "overview": overview,
        "trends": trends,
        "bs_variability": bs_variability,
        "bs_records": bs_records,
        "bp_records": bp_records,
        "med_records": med_records,
        "visit_records": visit_records,
        "report_date": datetime.now(),
        "period_start": week_ago,
        "period_end": datetime.now(),
    }
    
    # Render HTML
    env = Environment(loader=FileSystemLoader(str(TEMPLATES_DIR)))
    template = env.get_template("weekly_report.html")
    html_content = template.render(**context)
    
    # Generate PDF
    from weasyprint import HTML
    pdf_bytes = HTML(string=html_content).write_pdf()
    
    return pdf_bytes


async def generate_monthly_report(
    person_id: int,
    db: AsyncSession,
) -> bytes:
    """Generate monthly health report as PDF."""
    # Get person info
    person_stmt = select(Person).where(Person.id == person_id)
    person_result = await db.execute(person_stmt)
    person = person_result.scalar_one_or_none()
    
    if not person:
        raise ValueError("Person not found")
    
    # Get health overview
    overview = await get_health_overview(person_id, db)
    
    # Get trend alerts
    trends = await get_all_alerts(person_id, db)
    
    # Get blood sugar variability
    bs_variability = await analyze_blood_sugar_variability(person_id, days=30, db=db)
    
    # Get recent records
    month_ago = datetime.now() - timedelta(days=30)
    
    # Blood sugar records
    bs_stmt = (
        select(BloodSugarRecord)
        .where(BloodSugarRecord.person_id == person_id)
        .where(BloodSugarRecord.recorded_at >= month_ago)
        .order_by(BloodSugarRecord.recorded_at.desc())
    )
    bs_result = await db.execute(bs_stmt)
    bs_records = bs_result.scalars().all()
    
    # Blood pressure records
    bp_stmt = (
        select(BloodPressureRecord)
        .where(BloodPressureRecord.person_id == person_id)
        .where(BloodPressureRecord.recorded_at >= month_ago)
        .order_by(BloodPressureRecord.recorded_at.desc())
    )
    bp_result = await db.execute(bp_stmt)
    bp_records = bp_result.scalars().all()
    
    # Medication logs
    med_stmt = (
        select(MedicationLog)
        .where(MedicationLog.person_id == person_id)
        .where(MedicationLog.taken_at >= month_ago)
        .order_by(MedicationLog.taken_at.desc())
    )
    med_result = await db.execute(med_stmt)
    med_records = med_result.scalars().all()
    
    # Clinic visits
    visit_stmt = (
        select(Visit)
        .where(Visit.person_id == person_id)
        .where(Visit.visit_date >= month_ago.date())
        .order_by(Visit.visit_date.desc())
    )
    visit_result = await db.execute(visit_stmt)
    visit_records = visit_result.scalars().all()
    
    # Prepare template context
    context = {
        "person": person,
        "overview": overview,
        "trends": trends,
        "bs_variability": bs_variability,
        "bs_records": bs_records,
        "bp_records": bp_records,
        "med_records": med_records,
        "visit_records": visit_records,
        "report_date": datetime.now(),
        "period_start": month_ago,
        "period_end": datetime.now(),
    }
    
    # Render HTML
    env = Environment(loader=FileSystemLoader(str(TEMPLATES_DIR)))
    template = env.get_template("monthly_report.html")
    html_content = template.render(**context)
    
    # Generate PDF
    from weasyprint import HTML
    pdf_bytes = HTML(string=html_content).write_pdf()
    
    return pdf_bytes
