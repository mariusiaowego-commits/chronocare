"""Schemas — import all here."""

from chronocare.schemas.blood_sugar import (
    BloodSugarCreate,
    BloodSugarRead,
    BloodSugarUpdate,
)
from chronocare.schemas.cardiac import (
    BloodPressureCreate,
    BloodPressureRead,
    BloodPressureUpdate,
)
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
from chronocare.schemas.person import (
    ConditionCreate,
    ConditionRead,
    PersonCreate,
    PersonRead,
    PersonUpdate,
)
from chronocare.schemas.visit import VisitCreate, VisitRead, VisitUpdate

__all__ = [
    "BloodSugarCreate", "BloodSugarRead", "BloodSugarUpdate",
    "BloodPressureCreate", "BloodPressureRead", "BloodPressureUpdate",
    "MedicationCreate", "MedicationRead",
    "MedicationPlanCreate", "MedicationPlanRead", "MedicationPlanUpdate",
    "MedicationLogCreate", "MedicationLogRead",
    "PrescriptionCreate", "PrescriptionRead",
    "ConditionCreate", "ConditionRead",
    "PersonCreate", "PersonRead", "PersonUpdate",
    "VisitCreate", "VisitRead", "VisitUpdate",
]
