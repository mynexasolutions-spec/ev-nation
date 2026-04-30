from __future__ import annotations

from sqlalchemy import select, func
from sqlalchemy.orm import Session, joinedload

from app.models.order import Order, OrderItem


class OrderRepository:

    def _order_load_options(self):
        return (joinedload(Order.items),)

    def create(self, db: Session, order: Order) -> Order:
        db.add(order)
        db.commit()
        db.refresh(order)
        return order

    def get_by_id(self, db: Session, order_id: int) -> Order | None:
        return (
            db.query(Order)
            .filter(Order.id == order_id)
            .options(*self._order_load_options())
            .first()
        )

    def get_by_order_number(self, db: Session, order_number: str) -> Order | None:
        return (
            db.query(Order)
            .filter(Order.order_number == order_number)
            .options(*self._order_load_options())
            .first()
        )

    def get_by_razorpay_order_id(self, db: Session, razorpay_order_id: str) -> Order | None:
        return (
            db.query(Order)
            .filter(Order.razorpay_order_id == razorpay_order_id)
            .options(*self._order_load_options())
            .first()
        )

    def get_user_orders(
        self, db: Session, user_id: int, limit: int = 50, offset: int = 0,
    ) -> list[Order]:
        return (
            db.query(Order)
            .filter(Order.user_id == user_id)
            .options(*self._order_load_options())
            .order_by(Order.created_at.desc())
            .limit(limit)
            .offset(offset)
            .all()
        )

    def get_all_orders(
        self, db: Session, status_filter: str | None = None,
        limit: int = 50, offset: int = 0,
    ) -> list[Order]:
        q = db.query(Order).options(*self._order_load_options())
        if status_filter:
            q = q.filter(Order.status == status_filter)
        return q.order_by(Order.created_at.desc()).limit(limit).offset(offset).all()

    def count_all(self, db: Session, status_filter: str | None = None) -> int:
        q = db.query(func.count(Order.id))
        if status_filter:
            q = q.filter(Order.status == status_filter)
        return q.scalar() or 0

    def save(self, db: Session, order: Order) -> Order:
        db.add(order)
        db.commit()
        db.refresh(order)
        return order
