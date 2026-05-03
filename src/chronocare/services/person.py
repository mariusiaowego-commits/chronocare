"""Person CRUD service."""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from chronocare.models.person import Condition, Person
from chronocare.schemas.person import ConditionCreate, PersonCreate, PersonUpdate


# --- Person ---

async def list_persons(db: AsyncSession) -> list[Person]:
    """List all persons with conditions."""
    result = await db.execute(select(Person).options(selectinload(Person.conditions)).order_by(Person.id))
    return list(result.scalars().all())


async def get_person(db: AsyncSession, person_id: int) -> Person | None:
    """Get a single person by ID with conditions."""
    result = await db.execute(
        select(Person).options(selectinload(Person.conditions)).where(Person.id == person_id)
    )
    return result.scalar_one_or_none()


async def create_person(db: AsyncSession, data: PersonCreate) -> Person:
    """Create a new person and return it with conditions loaded."""
    person = Person(**data.model_dump())
    db.add(person)
    await db.commit()
    # Re-fetch with conditions eagerly loaded
    return await get_person(db, person.id)  # type: ignore[return-value]


async def update_person(db: AsyncSession, person_id: int, data: PersonUpdate) -> Person | None:
    """Update an existing person. Returns None if not found."""
    person = await get_person(db, person_id)
    if person is None:
        return None
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(person, field, value)
    await db.commit()
    # Re-fetch with conditions
    return await get_person(db, person_id)


async def delete_person(db: AsyncSession, person_id: int) -> bool:
    """Delete a person. Returns True if deleted."""
    person = await get_person(db, person_id)
    if person is None:
        return False
    await db.delete(person)
    await db.commit()
    return True


# --- Condition ---

async def add_condition(db: AsyncSession, person_id: int, data: ConditionCreate) -> Condition | None:
    """Add a condition to a person. Returns None if person not found."""
    person = await get_person(db, person_id)
    if person is None:
        return None
    condition = Condition(person_id=person_id, **data.model_dump())
    db.add(condition)
    await db.commit()
    await db.refresh(condition)
    return condition


async def list_conditions(db: AsyncSession, person_id: int) -> list[Condition]:
    """List conditions for a person."""
    result = await db.execute(
        select(Condition).where(Condition.person_id == person_id).order_by(Condition.created_at.desc())
    )
    return list(result.scalars().all())


async def delete_condition(db: AsyncSession, condition_id: int) -> bool:
    """Delete a condition."""
    result = await db.execute(select(Condition).where(Condition.id == condition_id))
    condition = result.scalar_one_or_none()
    if condition is None:
        return False
    await db.delete(condition)
    await db.commit()
    return True
