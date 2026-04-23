from sqlalchemy.orm import Session
from app.models.category import Category


class CategoryRepository:
    def get_all(self, db: Session, active_only: bool = False) -> list[Category]:
        query = db.query(Category)
        if active_only:
            query = query.filter(Category.is_active.is_(True))
        return query.order_by(Category.sort_order).all()

    def get_by_id(self, db: Session, category_id: int) -> Category | None:
        return db.query(Category).filter(Category.id == category_id).first()

    def get_by_slug(self, db: Session, slug: str) -> Category | None:
        return db.query(Category).filter(Category.slug == slug).first()

    def create(self, db: Session, category: Category) -> Category:
        db.add(category)
        db.commit()
        db.refresh(category)
        return category

    def update(self, db: Session, category: Category) -> Category:
        db.commit()
        db.refresh(category)
        return category

    def delete(self, db: Session, category: Category) -> None:
        db.delete(category)
        db.commit()


category_repository = CategoryRepository()
