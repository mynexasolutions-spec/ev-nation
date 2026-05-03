from __future__ import annotations

from sqlalchemy import Boolean, ForeignKey, Index, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base_class import Base
from app.models.mixins import IDMixin, TimestampMixin


class BlogCategory(IDMixin, TimestampMixin, Base):
    __tablename__ = "blog_categories"

    name: Mapped[str] = mapped_column(String(120), nullable=False, unique=True)
    slug: Mapped[str] = mapped_column(String(120), nullable=False, unique=True, index=True)

    posts: Mapped[list["BlogPost"]] = relationship(
        back_populates="category", cascade="all, delete-orphan"
    )


class BlogPost(IDMixin, TimestampMixin, Base):
    __tablename__ = "blog_posts"
    __table_args__ = (
        Index("ix_blog_posts_slug", "slug", unique=True),
        Index("ix_blog_posts_created_at", "created_at"),
    )

    title: Mapped[str] = mapped_column(String(255), nullable=False)
    slug: Mapped[str] = mapped_column(String(255), nullable=False, unique=True, index=True)
    primary_image: Mapped[str | None] = mapped_column(String(500), nullable=True)
    short_description: Mapped[str | None] = mapped_column(String(500), nullable=True)
    content: Mapped[str | None] = mapped_column(Text, nullable=True)
    author: Mapped[str | None] = mapped_column(String(120), nullable=True, default="EV Nation Team")
    read_time: Mapped[int | None] = mapped_column(nullable=True)  # minutes

    category_id: Mapped[int | None] = mapped_column(
        ForeignKey("blog_categories.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    is_featured: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, server_default="0")
    is_published: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, server_default="0")

    category: Mapped["BlogCategory | None"] = relationship(back_populates="posts")


class BlogSubscriber(IDMixin, TimestampMixin, Base):
    __tablename__ = "blog_subscribers"

    email: Mapped[str] = mapped_column(String(255), nullable=False, unique=True, index=True)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True, server_default="1")
