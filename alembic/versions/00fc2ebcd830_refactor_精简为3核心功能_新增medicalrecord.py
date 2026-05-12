"""refactor: 精简为3核心功能，新增MedicalRecord

Revision ID: 00fc2ebcd830
Revises: 0fb40be5fdc6
Create Date: 2026-05-09 22:56:01.406741

"""
from collections.abc import Sequence

from alembic import op

# revision identifiers, used by Alembic.
revision: str = '00fc2ebcd830'
down_revision: str | Sequence[str] | None = '0fb40be5fdc6'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""
    # Create medical_records table (IF NOT EXISTS)
    op.execute("""
        CREATE TABLE IF NOT EXISTS medical_records (
            id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
            person_id INTEGER NOT NULL,
            record_type TEXT NOT NULL,
            visit_date DATE,
            hospital TEXT,
            department TEXT,
            doctor TEXT,
            image_path TEXT,
            ocr_text TEXT,
            structured_data JSON,
            doctor_orders JSON,
            lab_results JSON,
            notes TEXT,
            created_at DATETIME DEFAULT (CURRENT_TIMESTAMP) NOT NULL,
            updated_at DATETIME DEFAULT (CURRENT_TIMESTAMP) NOT NULL,
            FOREIGN KEY(person_id) REFERENCES persons (id)
        )
    """)

    # Drop old tables (use IF EXISTS to handle missing tables)
    tables_to_drop = [
        'wiki_fts_idx', 'wiki_fts_docsize', 'wiki_fts_data', 'wiki_fts_config', 'wiki_fts',
        'wiki_articles', 'wiki_categories',
        'news_items', 'rss_feeds',
        'medication_logs', 'medication_plans', 'medications', 'prescriptions',
        'blood_pressure_records',
    ]
    for table in tables_to_drop:
        op.execute(f"DROP TABLE IF EXISTS {table}")


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_table('medical_records')
