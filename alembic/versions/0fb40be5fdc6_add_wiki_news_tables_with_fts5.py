"""add wiki/news tables with FTS5

Revision ID: 0fb40be5fdc6
Revises: 0e22736987d9
Create Date: 2026-05-04 00:10:36.319669

"""
from collections.abc import Sequence

from alembic import op

# revision identifiers, used by Alembic.
revision: str = '0fb40be5fdc6'
down_revision: str | Sequence[str] | None = '0e22736987d9'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""
    # Create FTS5 virtual table for wiki full-text search
    op.execute("""
        CREATE VIRTUAL TABLE IF NOT EXISTS wiki_fts USING fts5(
            title, content, tags,
            content=wiki_articles,
            content_rowid=id
        )
    """)
    
    # Populate FTS index from existing articles
    op.execute("""
        INSERT INTO wiki_fts(rowid, title, content, tags)
        SELECT id, title, content, COALESCE(tags, '') FROM wiki_articles
    """)


def downgrade() -> None:
    """Downgrade schema."""
    op.execute("DROP TABLE IF EXISTS wiki_fts")
