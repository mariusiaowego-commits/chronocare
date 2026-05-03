"""Wiki (knowledge base) models."""

from datetime import datetime

from sqlalchemy import Boolean, ForeignKey, JSON, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from chronocare.models.base import Base


class WikiCategory(Base):
    """知识分类"""

    __tablename__ = "wiki_categories"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(Text, nullable=False)
    slug: Mapped[str] = mapped_column(Text, nullable=False, unique=True)
    parent_id: Mapped[int | None] = mapped_column(ForeignKey("wiki_categories.id"))
    description: Mapped[str | None] = mapped_column(Text)
    icon: Mapped[str | None] = mapped_column(Text)
    sort_order: Mapped[int] = mapped_column(default=0)


class WikiArticle(Base):
    """知识条目"""

    __tablename__ = "wiki_articles"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    title: Mapped[str] = mapped_column(Text, nullable=False)
    slug: Mapped[str] = mapped_column(Text, nullable=False, unique=True)
    content: Mapped[str] = mapped_column(Text, nullable=False)  # Markdown
    category_id: Mapped[int | None] = mapped_column(ForeignKey("wiki_categories.id"))
    tags: Mapped[dict | None] = mapped_column(JSON)  # JSON array
    source: Mapped[str | None] = mapped_column(Text)
    source_url: Mapped[str | None] = mapped_column(Text)
    related_conditions: Mapped[dict | None] = mapped_column(JSON)  # JSON array
    related_persons: Mapped[dict | None] = mapped_column(JSON)  # JSON array
    is_recommended: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(server_default=func.now(), onupdate=func.now())
