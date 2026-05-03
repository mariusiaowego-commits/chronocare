"""Visit CRUD service."""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from chronocare.models.visit import Visit
from chronocare.schemas.visit import VisitCreate, VisitUpdate


async def list_visits(db: AsyncSession, person_id: int | None = None) -> list[Visit]:
    stmt = select(Visit).order_by(Visit.visit_date.desc())
    if person_id is not None:
        stmt = stmt.where(Visit.person_id == person_id)
    result = await db.execute(stmt)
    return list(result.scalars().all())


async def get_visit(db: AsyncSession, visit_id: int) -> Visit | None:
    result = await db.execute(select(Visit).where(Visit.id == visit_id))
    return result.scalar_one_or_none()


async def create_visit(db: AsyncSession, data: VisitCreate) -> Visit:
    visit = Visit(**data.model_dump())
    db.add(visit)
    await db.commit()
    await db.refresh(visit)
    return visit


async def update_visit(db: AsyncSession, visit_id: int, data: VisitUpdate) -> Visit | None:
    visit = await get_visit(db, visit_id)
    if visit is None:
        return None
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(visit, field, value)
    await db.commit()
    await db.refresh(visit)
    return visit


async def delete_visit(db: AsyncSession, visit_id: int) -> bool:
    visit = await get_visit(db, visit_id)
    if visit is None:
        return False
    await db.delete(visit)
    await db.commit()
    return True
