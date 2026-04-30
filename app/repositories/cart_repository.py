from __future__ import annotations

from sqlalchemy import and_
from sqlalchemy.orm import Session, joinedload

from app.models.cart import CartItem


class CartRepository:

    def get_user_cart(self, db: Session, user_id: int) -> list[CartItem]:
        return (
            db.query(CartItem)
            .filter(CartItem.user_id == user_id)
            .options(
                joinedload(CartItem.product),
                joinedload(CartItem.variant),
            )
            .all()
        )

    def get_item(self, db: Session, item_id: int, user_id: int) -> CartItem | None:
        return (
            db.query(CartItem)
            .filter(CartItem.id == item_id, CartItem.user_id == user_id)
            .first()
        )

    def find_existing(
        self,
        db: Session,
        user_id: int,
        product_id: int,
        variant_id: int | None,
        attributes: dict | None = None,
    ) -> CartItem | None:
        conditions = [
            CartItem.user_id == user_id,
            CartItem.product_id == product_id,
        ]
        if variant_id is not None:
            conditions.append(CartItem.variant_id == variant_id)
        else:
            conditions.append(CartItem.variant_id.is_(None))
        
        # Attributes check (simplified comparison)
        if attributes:
            conditions.append(CartItem.attributes == attributes)
        else:
            conditions.append(CartItem.attributes.is_(None))
            
        return db.query(CartItem).filter(and_(*conditions)).first()

    def add_item(
        self,
        db: Session,
        user_id: int,
        product_id: int,
        variant_id: int | None,
        quantity: int,
        attributes: dict | None = None,
    ) -> CartItem:
        existing = self.find_existing(db, user_id, product_id, variant_id, attributes)
        if existing:
            existing.quantity = min(existing.quantity + quantity, 10)
            db.add(existing)
            db.commit()
            db.refresh(existing)
            return existing

        item = CartItem(
            user_id=user_id,
            product_id=product_id,
            variant_id=variant_id,
            quantity=quantity,
            attributes=attributes,
        )
        db.add(item)
        db.commit()
        db.refresh(item)
        return item

    def update_quantity(
        self, db: Session, item_id: int, user_id: int, quantity: int,
    ) -> CartItem | None:
        item = self.get_item(db, item_id, user_id)
        if item is None:
            return None
        item.quantity = quantity
        db.add(item)
        db.commit()
        db.refresh(item)
        return item

    def remove_item(self, db: Session, item_id: int, user_id: int) -> bool:
        item = self.get_item(db, item_id, user_id)
        if item is None:
            return False
        db.delete(item)
        db.commit()
        return True

    def clear_cart(self, db: Session, user_id: int) -> int:
        count = (
            db.query(CartItem)
            .filter(CartItem.user_id == user_id)
            .delete(synchronize_session="fetch")
        )
        db.commit()
        return count

    def count_items(self, db: Session, user_id: int) -> int:
        return (
            db.query(CartItem)
            .filter(CartItem.user_id == user_id)
            .count()
        )
