"""Schemas — import all here."""

from chronocare.schemas.blood_sugar import (
    BloodSugarCreate,
    BloodSugarRead,
    BloodSugarUpdate,
)
from chronocare.schemas.medical_record import (
    MedicalRecordCreate,
    MedicalRecordRead,
    MedicalRecordUpdate,
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
    "MedicalRecordCreate", "MedicalRecordRead", "MedicalRecordUpdate",
    "ConditionCreate", "ConditionRead",
    "PersonCreate", "PersonRead", "PersonUpdate",
    "VisitCreate", "VisitRead", "VisitUpdate",
]
