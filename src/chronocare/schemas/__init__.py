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
from chronocare.schemas.news import (
    NewsItemBrief,
    NewsItemCreate,
    NewsItemRead,
    NewsItemUpdate,
    RssFeedCreate,
    RssFeedRead,
    RssFeedUpdate,
)
from chronocare.schemas.person import (
    ConditionCreate,
    ConditionRead,
    PersonCreate,
    PersonRead,
    PersonUpdate,
)
from chronocare.schemas.visit import VisitCreate, VisitRead, VisitUpdate
from chronocare.schemas.wiki import (
    WikiArticleBrief,
    WikiArticleCreate,
    WikiArticleRead,
    WikiArticleUpdate,
    WikiCategoryCreate,
    WikiCategoryRead,
    WikiCategoryUpdate,
    WikiSearchParams,
)

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
    "WikiCategoryCreate", "WikiCategoryRead", "WikiCategoryUpdate",
    "WikiArticleCreate", "WikiArticleRead", "WikiArticleUpdate", "WikiArticleBrief",
    "WikiSearchParams",
    "NewsItemCreate", "NewsItemRead", "NewsItemUpdate", "NewsItemBrief",
    "RssFeedCreate", "RssFeedRead", "RssFeedUpdate",
]
