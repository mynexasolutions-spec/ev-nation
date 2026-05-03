from __future__ import annotations

import re

from sqlalchemy.orm import Session

from app.models.blog import BlogCategory, BlogPost, BlogSubscriber
from app.repositories.blog_repository import blog_repo


def _slugify(text: str) -> str:
    text = text.lower().strip()
    text = re.sub(r"[^\w\s-]", "", text)
    text = re.sub(r"[\s_]+", "-", text)
    text = re.sub(r"-+", "-", text).strip("-")
    return text


class BlogService:
    # ── Categories ──

    def get_all_categories(self, db: Session) -> list[BlogCategory]:
        return blog_repo.get_all_categories(db)

    def get_or_create_category(self, db: Session, name: str) -> BlogCategory:
        existing = blog_repo.get_category_by_name(db, name)
        if existing:
            return existing
        slug = _slugify(name)
        # Ensure slug uniqueness
        base = slug
        i = 1
        while blog_repo.get_category_by_slug(db, slug):
            slug = f"{base}-{i}"
            i += 1
        return blog_repo.create_category(db, name=name, slug=slug)

    def delete_category(self, db: Session, category_id: int) -> bool:
        return blog_repo.delete_category(db, category_id)

    # ── Posts ──

    def list_admin(self, db: Session) -> list[BlogPost]:
        return blog_repo.get_all_admin(db)

    def list_published(self, db: Session, category_slug: str | None = None) -> list[BlogPost]:
        return blog_repo.get_published(db, category_slug=category_slug)

    def get_featured(self, db: Session, limit: int = 3) -> list[BlogPost]:
        return blog_repo.get_featured(db, limit=limit)

    def get_latest(self, db: Session, limit: int = 5) -> list[BlogPost]:
        return blog_repo.get_latest(db, limit=limit)

    def get_related(self, db: Session, post_id: int, category_id: int | None, limit: int = 4) -> list[BlogPost]:
        return blog_repo.get_related(db, post_id=post_id, category_id=category_id, limit=limit)

    def get_by_slug(self, db: Session, slug: str) -> BlogPost | None:
        return blog_repo.get_by_slug(db, slug)

    def get_by_id(self, db: Session, post_id: int) -> BlogPost | None:
        return blog_repo.get_by_id(db, post_id)

    def _unique_slug(self, db: Session, base_slug: str, exclude_id: int | None = None) -> str:
        slug = base_slug
        i = 1
        while True:
            existing = blog_repo.get_by_slug(db, slug)
            if not existing or (exclude_id and existing.id == exclude_id):
                break
            slug = f"{base_slug}-{i}"
            i += 1
        return slug

    def create(self, db: Session, data: dict) -> BlogPost:
        slug = self._unique_slug(db, _slugify(data.get("title", "")))
        data.setdefault("slug", slug)
        return blog_repo.create(db, **data)

    def update(self, db: Session, post_id: int, data: dict) -> BlogPost | None:
        post = blog_repo.get_by_id(db, post_id)
        if not post:
            return None
        if "title" in data and "slug" not in data:
            data["slug"] = self._unique_slug(db, _slugify(data["title"]), exclude_id=post_id)
        return blog_repo.update(db, post, **data)

    def delete(self, db: Session, post_id: int) -> bool:
        return blog_repo.delete(db, post_id)

    def set_primary_image(self, db: Session, post_id: int, image_path: str) -> BlogPost | None:
        post = blog_repo.get_by_id(db, post_id)
        if not post:
            return None
        return blog_repo.update(db, post, primary_image=image_path)

    # ── Subscribers ──

    def subscribe(self, db: Session, email: str) -> tuple[BlogSubscriber, bool]:
        """Returns (subscriber, created). created=False if already exists."""
        existing = blog_repo.get_subscriber_by_email(db, email)
        if existing:
            return existing, False
        return blog_repo.create_subscriber(db, email), True

    def get_all_subscribers(self, db: Session) -> list[BlogSubscriber]:
        return blog_repo.get_all_subscribers(db)

    def delete_subscriber(self, db: Session, sub_id: int) -> bool:
        return blog_repo.delete_subscriber(db, sub_id)


blog_service = BlogService()
