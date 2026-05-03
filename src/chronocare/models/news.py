"""News / RSS models."""

from datetime import datetime

from sqlalchemy import Boolean, JSON, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from chronocare.models.base import Base


class NewsItem(Base):
    """新闻资讯"""

    __tablename__ = "news_items"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    title: Mapped[str] = mapped_column(Text, nullable=False)
    url: Mapped[str | None] = mapped_column(Text)
    source: Mapped[str | None] = mapped_column(Text)
    content: Mapped[str | None] = mapped_column(Text)  # 本地存档
    summary: Mapped[str | None] = mapped_column(Text)
    published_at: Mapped[datetime | None]
    category: Mapped[str | None] = mapped_column(Text)
    tags: Mapped[dict | None] = mapped_column(JSON)  # JSON array
    is_bookmarked: Mapped[bool] = mapped_column(Boolean, default=False)
    is_shared: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())


class RssFeed(Base):
    """RSS 源配置"""

    __tablename__ = "rss_feeds"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(Text, nullable=False)
    url: Mapped[str] = mapped_column(Text, nullable=False)
    category: Mapped[str | None] = mapped_column(Text)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    last_fetched_at: Mapped[datetime | None]
    fetch_interval_hours: Mapped[int] = mapped_column(default=4)
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())
