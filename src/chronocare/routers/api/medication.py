"""Medication REST API endpoints."""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from chronocare.database import get_db
from chronocare.schemas.medication import (
    MedicationCreate,
    MedicationLogCreate,
    MedicationLogRead,
    MedicationPlanCreate,
    MedicationPlanRead,
    MedicationPlanUpdate,
    MedicationRead,
    PrescriptionCreate,
    PrescriptionRead,
)
from chronocare.services.medication import (
    create_log,
    create_medication,
    create_plan,
    create_prescription,
    delete_plan,
    delete_prescription,
    list_logs,
    list_medications,
    list_plans,
    list_prescriptions,
    update_plan,
)

router = APIRouter(prefix="/api/medications", tags=["medications"])


# --- Medications ---

@router.get("", response_model=list[MedicationRead])
async def api_list_meds(db: AsyncSession = Depends(get_db)):
    return await list_medications(db)


@router.post("", response_model=MedicationRead, status_code=201)
async def api_create_med(data: MedicationCreate, db: AsyncSession = Depends(get_db)):
    return await create_medication(db, data)


# --- Plans ---

@router.get("/plans", response_model=list[MedicationPlanRead])
async def api_list_plans(person_id: int | None = Query(None), db: AsyncSession = Depends(get_db)):
    return await list_plans(db, person_id)


@router.post("/plans", response_model=MedicationPlanRead, status_code=201)
async def api_create_plan(data: MedicationPlanCreate, db: AsyncSession = Depends(get_db)):
    return await create_plan(db, data)


@router.patch("/plans/{plan_id}", response_model=MedicationPlanRead)
async def api_update_plan(plan_id: int, data: MedicationPlanUpdate, db: AsyncSession = Depends(get_db)):
    plan = await update_plan(db, plan_id, data)
    if plan is None:
        raise HTTPException(404, "Plan not found")
    return plan


@router.delete("/plans/{plan_id}", status_code=204)
async def api_delete_plan(plan_id: int, db: AsyncSession = Depends(get_db)):
    if not await delete_plan(db, plan_id):
        raise HTTPException(404, "Plan not found")


# --- Logs ---

@router.get("/plans/{plan_id}/logs", response_model=list[MedicationLogRead])
async def api_list_logs(plan_id: int, db: AsyncSession = Depends(get_db)):
    return await list_logs(db, plan_id)


@router.post("/logs", response_model=MedicationLogRead, status_code=201)
async def api_create_log(data: MedicationLogCreate, db: AsyncSession = Depends(get_db)):
    return await create_log(db, data)


# --- Prescriptions ---

@router.get("/prescriptions", response_model=list[PrescriptionRead])
async def api_list_rx(person_id: int | None = Query(None), db: AsyncSession = Depends(get_db)):
    return await list_prescriptions(db, person_id)


@router.post("/prescriptions", response_model=PrescriptionRead, status_code=201)
async def api_create_rx(data: PrescriptionCreate, db: AsyncSession = Depends(get_db)):
    return await create_prescription(db, data)


@router.delete("/prescriptions/{rx_id}", status_code=204)
async def api_delete_rx(rx_id: int, db: AsyncSession = Depends(get_db)):
    if not await delete_prescription(db, rx_id):
        raise HTTPException(404, "Prescription not found")
