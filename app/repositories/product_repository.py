from sqlalchemy import select, func
from sqlalchemy.orm import Session, selectinload

from app.models.product import Product, Variant


class ProductRepository:
    def _product_load_options(self):
        return (
            selectinload(Product.images),
            selectinload(Product.variants),
            selectinload(Product.spec),
            selectinload(Product.battery_options),
            selectinload(Product.extra_specs),
            selectinload(Product.category),
        )

    def list_active(self, db: Session) -> list[Product]:
        statement = (
            select(Product)
            .where(Product.is_active.is_(True))
            .options(*self._product_load_options())
            .order_by(Product.sort_order.asc(), Product.id.asc())
        )
        return list(db.scalars(statement).unique())

    def get_random_active_exclude(self, db: Session, exclude_id: int, limit: int = 3) -> list[Product]:
        statement = (
            select(Product)
            .where(Product.is_active.is_(True), Product.id != exclude_id)
            .options(*self._product_load_options())
            .order_by(func.random())
            .limit(limit)
        )
        return list(db.scalars(statement).unique())

    def list_all(self, db: Session) -> list[Product]:
        statement = select(Product).options(*self._product_load_options()).order_by(Product.sort_order.asc(), Product.id.asc())
        return list(db.scalars(statement).unique())

    def get_active_by_slug(self, db: Session, slug: str) -> Product | None:
        statement = (
            select(Product)
            .where(Product.slug == slug, Product.is_active.is_(True))
            .options(*self._product_load_options())
        )
        return db.scalar(statement)

    def get_by_slug(self, db: Session, slug: str) -> Product | None:
        statement = select(Product).where(Product.slug == slug).options(*self._product_load_options())
        return db.scalar(statement)

    def get_by_id(self, db: Session, product_id: int) -> Product | None:
        statement = select(Product).where(Product.id == product_id).options(*self._product_load_options())
        return db.scalar(statement)

    def get_variant_by_id(self, db: Session, variant_id: int) -> Variant | None:
        statement = select(Variant).where(Variant.id == variant_id).options(selectinload(Variant.product))
        return db.scalar(statement)

    def save(self, db: Session, product: Product) -> Product:
        db.add(product)
        db.commit()
        db.refresh(product)
        return self.get_by_id(db, product.id) or product
