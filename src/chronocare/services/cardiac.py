"""Cardiac records CRUD service."""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from chronocare.models.cardiac import BloodPressureRecord
from chronocare.schemas.cardiac import BloodPressureCreate, BloodPressureUpdate


async def list_bp(db: AsyncSession, person_id: int | None = None) -> list[BloodPressureRecord]:
    stmt = select(BloodPressureRecord).order_by(BloodPressureRecord.measured_at.desc())
    if person_id is not None:
        stmt = stmt.where(BloodPressureRecord.person_id == person_id)
    result = await db.execute(stmt)
    return list(result.scalars().all())


async def get_bp(db: AsyncSession, record_id: int) -> BloodPressureRecord | None:
    result = await db.execute(select(BloodPressureRecord).where(BloodPressureRecord.id == record_id))
    return result.scalar_one_or_none()


async def create_bp(db: AsyncSession, data: BloodPressureCreate) -> BloodPressureRecord:
    record = BloodPressureRecord(**data.model_dump())
    db.add(record)
    await db.commit()
    await db.refresh(record)
    return record


async def update_bp(db: AsyncSession, record_id: int, data: BloodPressureUpdate) -> BloodPressureRecord | None:
    record = await get_bp(db, record_id)
    if record is None:
        return None
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(record, field, value)
    await db.commit()
    await db.refresh(record)
    return record


async def delete_bp(db: AsyncSession, record_id: int) -> bool:
    record = await get_bp(db, record_id)
    if record is None:
        return False
    await db.delete(record)
    await db.commit()
    return True
