"""Medication CRUD service."""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from chronocare.models.medication import Medication, MedicationLog, MedicationPlan, Prescription
from chronocare.schemas.medication import (
    MedicationCreate,
    MedicationLogCreate,
    MedicationPlanCreate,
    MedicationPlanUpdate,
    PrescriptionCreate,
)

# --- Medication ---

async def list_medications(db: AsyncSession) -> list[Medication]:
    result = await db.execute(select(Medication).order_by(Medication.name))
    return list(result.scalars().all())


async def get_medication(db: AsyncSession, med_id: int) -> Medication | None:
    result = await db.execute(select(Medication).where(Medication.id == med_id))
    return result.scalar_one_or_none()


async def create_medication(db: AsyncSession, data: MedicationCreate) -> Medication:
    med = Medication(**data.model_dump())
    db.add(med)
    await db.commit()
    await db.refresh(med)
    return med


# --- Medication Plan ---

async def list_plans(db: AsyncSession, person_id: int | None = None) -> list[MedicationPlan]:
    stmt = (
        select(MedicationPlan)
        .options(selectinload(MedicationPlan.medication))
        .order_by(MedicationPlan.start_date.desc())
    )
    if person_id is not None:
        stmt = stmt.where(MedicationPlan.person_id == person_id)
    result = await db.execute(stmt)
    return list(result.scalars().all())


async def get_plan(db: AsyncSession, plan_id: int) -> MedicationPlan | None:
    result = await db.execute(
        select(MedicationPlan).options(selectinload(MedicationPlan.medication)).where(MedicationPlan.id == plan_id)
    )
    return result.scalar_one_or_none()


async def create_plan(db: AsyncSession, data: MedicationPlanCreate) -> MedicationPlan:
    plan = MedicationPlan(**data.model_dump())
    db.add(plan)
    await db.commit()
    return (await get_plan(db, plan.id))  # type: ignore[return-value]


async def update_plan(db: AsyncSession, plan_id: int, data: MedicationPlanUpdate) -> MedicationPlan | None:
    plan = await get_plan(db, plan_id)
    if plan is None:
        return None
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(plan, field, value)
    await db.commit()
    return (await get_plan(db, plan_id))


async def delete_plan(db: AsyncSession, plan_id: int) -> bool:
    plan = await get_plan(db, plan_id)
    if plan is None:
        return False
    await db.delete(plan)
    await db.commit()
    return True


# --- Medication Log ---

async def create_log(db: AsyncSession, data: MedicationLogCreate) -> MedicationLog:
    log = MedicationLog(**data.model_dump())
    db.add(log)
    await db.commit()
    await db.refresh(log)
    return log


async def list_logs(db: AsyncSession, plan_id: int) -> list[MedicationLog]:
    result = await db.execute(
        select(MedicationLog).where(MedicationLog.plan_id == plan_id).order_by(MedicationLog.taken_at.desc())
    )
    return list(result.scalars().all())


# --- Prescription ---

async def list_prescriptions(db: AsyncSession, person_id: int | None = None) -> list[Prescription]:
    stmt = select(Prescription).order_by(Prescription.prescription_date.desc())
    if person_id is not None:
        stmt = stmt.where(Prescription.person_id == person_id)
    result = await db.execute(stmt)
    return list(result.scalars().all())


async def create_prescription(db: AsyncSession, data: PrescriptionCreate) -> Prescription:
    rx = Prescription(**data.model_dump())
    db.add(rx)
    await db.commit()
    await db.refresh(rx)
    return rx


async def delete_prescription(db: AsyncSession, rx_id: int) -> bool:
    result = await db.execute(select(Prescription).where(Prescription.id == rx_id))
    rx = result.scalar_one_or_none()
    if rx is None:
        return False
    await db.delete(rx)
    await db.commit()
    return True
