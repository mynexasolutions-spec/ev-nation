from __future__ import annotations

from sqlalchemy import func, select
from sqlalchemy.orm import Session, selectinload

from app.models.blog import BlogCategory, BlogPost, BlogSubscriber


class BlogRepository:
    # ── Categories ──

    def get_all_categories(self, db: Session) -> list[BlogCategory]:
        return db.execute(select(BlogCategory).order_by(BlogCategory.name)).scalars().all()

    def get_category_by_slug(self, db: Session, slug: str) -> BlogCategory | None:
        return db.execute(select(BlogCategory).where(BlogCategory.slug == slug)).scalar_one_or_none()

    def get_category_by_name(self, db: Session, name: str) -> BlogCategory | None:
        return db.execute(
            select(BlogCategory).where(func.lower(BlogCategory.name) == name.lower())
        ).scalar_one_or_none()

    def create_category(self, db: Session, name: str, slug: str) -> BlogCategory:
        cat = BlogCategory(name=name, slug=slug)
        db.add(cat)
        db.commit()
        db.refresh(cat)
        return cat

    def delete_category(self, db: Session, category_id: int) -> bool:
        cat = db.get(BlogCategory, category_id)
        if not cat:
            return False
        db.delete(cat)
        db.commit()
        return True

    # ── Blog Posts ──

    def _base_query(self):
        return select(BlogPost).options(selectinload(BlogPost.category))

    def get_all_admin(self, db: Session) -> list[BlogPost]:
        return (
            db.execute(self._base_query().order_by(BlogPost.created_at.desc()))
            .scalars()
            .all()
        )

    def get_published(self, db: Session, category_slug: str | None = None, limit: int = 100) -> list[BlogPost]:
        q = self._base_query().where(BlogPost.is_published == True)
        if category_slug:
            q = q.join(BlogCategory).where(BlogCategory.slug == category_slug)
        q = q.order_by(BlogPost.created_at.desc()).limit(limit)
        return db.execute(q).scalars().all()

    def get_featured(self, db: Session, limit: int = 3) -> list[BlogPost]:
        return (
            db.execute(
                self._base_query()
                .where(BlogPost.is_published == True, BlogPost.is_featured == True)
                .order_by(BlogPost.created_at.desc())
                .limit(limit)
            )
            .scalars()
            .all()
        )

    def get_latest(self, db: Session, limit: int = 5) -> list[BlogPost]:
        return (
            db.execute(
                self._base_query()
                .where(BlogPost.is_published == True)
                .order_by(BlogPost.created_at.desc())
                .limit(limit)
            )
            .scalars()
            .all()
        )

    def get_related(self, db: Session, post_id: int, category_id: int | None, limit: int = 4) -> list[BlogPost]:
        q = self._base_query().where(
            BlogPost.is_published == True, BlogPost.id != post_id
        )
        if category_id:
            q = q.where(BlogPost.category_id == category_id)
        return db.execute(q.order_by(BlogPost.created_at.desc()).limit(limit)).scalars().all()

    def get_by_slug(self, db: Session, slug: str) -> BlogPost | None:
        return db.execute(self._base_query().where(BlogPost.slug == slug)).scalar_one_or_none()

    def get_by_id(self, db: Session, post_id: int) -> BlogPost | None:
        return db.execute(self._base_query().where(BlogPost.id == post_id)).scalar_one_or_none()

    def create(self, db: Session, **kwargs) -> BlogPost:
        post = BlogPost(**kwargs)
        db.add(post)
        db.commit()
        db.refresh(post)
        return post

    def update(self, db: Session, post: BlogPost, **kwargs) -> BlogPost:
        for k, v in kwargs.items():
            setattr(post, k, v)
        db.commit()
        db.refresh(post)
        return post

    def delete(self, db: Session, post_id: int) -> bool:
        post = db.get(BlogPost, post_id)
        if not post:
            return False
        db.delete(post)
        db.commit()
        return True

    # ── Subscribers ──

    def get_subscriber_by_email(self, db: Session, email: str) -> BlogSubscriber | None:
        return db.execute(
            select(BlogSubscriber).where(BlogSubscriber.email == email.lower())
        ).scalar_one_or_none()

    def create_subscriber(self, db: Session, email: str) -> BlogSubscriber:
        sub = BlogSubscriber(email=email.lower())
        db.add(sub)
        db.commit()
        db.refresh(sub)
        return sub

    def get_all_subscribers(self, db: Session) -> list[BlogSubscriber]:
        return (
            db.execute(select(BlogSubscriber).order_by(BlogSubscriber.created_at.desc()))
            .scalars()
            .all()
        )

    def delete_subscriber(self, db: Session, sub_id: int) -> bool:
        sub = db.get(BlogSubscriber, sub_id)
        if not sub:
            return False
        db.delete(sub)
        db.commit()
        return True


blog_repo = BlogRepository()
