from sqlalchemy.orm import Session

from app.core.errors import DomainValidationError, NotFoundError
from app.core.normalization import normalize_slug
from app.models.category import Category
from app.repositories.category_repository import category_repository
from app.schemas.category import CategoryCreate, CategoryUpdate


class CategoryService:
    def __init__(self, repository=category_repository):
        self.repository = repository

    def get_all_active(self, db: Session) -> list[Category]:
        return self.repository.get_all(db, active_only=True)

    def get_all_admin(self, db: Session) -> list[Category]:
        return self.repository.get_all(db, active_only=False)

    def get_by_id(self, db: Session, category_id: int) -> Category:
        category = self.repository.get_by_id(db, category_id)
        if not category:
            raise NotFoundError(f"Category {category_id} not found.")
        return category

    def create(self, db: Session, payload: CategoryCreate) -> Category:
        slug = payload.slug or normalize_slug(payload.name)
        if not slug:
            raise DomainValidationError("Category slug could not be generated.")
        
        if self.repository.get_by_slug(db, slug):
            raise DomainValidationError(f"Category slug '{slug}' is already in use.")

        category = Category(
            name=payload.name,
            description=payload.description,
            slug=slug,
            sort_order=payload.sort_order,
            is_active=payload.is_active,
        )
        return self.repository.create(db, category)

    def update(self, db: Session, category_id: int, payload: CategoryUpdate) -> Category:
        category = self.get_by_id(db, category_id)
        
        if payload.name is not None:
            category.name = payload.name
        if payload.description is not None:
            category.description = payload.description
        if payload.sort_order is not None:
            category.sort_order = payload.sort_order
        if payload.is_active is not None:
            category.is_active = payload.is_active

        return self.repository.update(db, category)

    def delete(self, db: Session, category_id: int) -> None:
        category = self.get_by_id(db, category_id)
        self.repository.delete(db, category)


category_service = CategoryService()
