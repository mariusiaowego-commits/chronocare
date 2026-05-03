"""Blood sugar CRUD service."""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from chronocare.models.blood_sugar import BloodSugarRecord
from chronocare.schemas.blood_sugar import BloodSugarCreate, BloodSugarUpdate


async def list_blood_sugar(db: AsyncSession, person_id: int | None = None) -> list[BloodSugarRecord]:
    """List blood sugar records, optionally filtered by person."""
    stmt = select(BloodSugarRecord).order_by(BloodSugarRecord.measured_at.desc())
    if person_id is not None:
        stmt = stmt.where(BloodSugarRecord.person_id == person_id)
    result = await db.execute(stmt)
    return list(result.scalars().all())


async def get_blood_sugar(db: AsyncSession, record_id: int) -> BloodSugarRecord | None:
    result = await db.execute(select(BloodSugarRecord).where(BloodSugarRecord.id == record_id))
    return result.scalar_one_or_none()


async def create_blood_sugar(db: AsyncSession, data: BloodSugarCreate) -> BloodSugarRecord:
    record = BloodSugarRecord(**data.model_dump())
    db.add(record)
    await db.commit()
    await db.refresh(record)
    return record


async def update_blood_sugar(db: AsyncSession, record_id: int, data: BloodSugarUpdate) -> BloodSugarRecord | None:
    record = await get_blood_sugar(db, record_id)
    if record is None:
        return None
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(record, field, value)
    await db.commit()
    await db.refresh(record)
    return record


async def delete_blood_sugar(db: AsyncSession, record_id: int) -> bool:
    record = await get_blood_sugar(db, record_id)
    if record is None:
        return False
    await db.delete(record)
    await db.commit()
    return True
