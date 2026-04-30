from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, Enum, ForeignKey, Index, Integer, String, Text, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base_class import Base
from app.models.enums import OrderStatus, PaymentStatus
from app.models.mixins import IDMixin, TimestampMixin


class Order(IDMixin, TimestampMixin, Base):
    __tablename__ = "orders"
    __table_args__ = (
        Index("ix_orders_user_id", "user_id"),
        Index("ix_orders_status", "status"),
        Index("ix_orders_created_at", "created_at"),
    )

    order_number: Mapped[str] = mapped_column(
        String(50), unique=True, index=True, nullable=False,
    )
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    status: Mapped[OrderStatus] = mapped_column(
        Enum(OrderStatus, name="order_status_enum"),
        nullable=False,
        default=OrderStatus.PENDING,
        server_default=OrderStatus.PENDING.value,
    )
    payment_status: Mapped[PaymentStatus] = mapped_column(
        Enum(PaymentStatus, name="payment_status_enum"),
        nullable=False,
        default=PaymentStatus.PENDING,
        server_default=PaymentStatus.PENDING.value,
    )

    # Razorpay fields
    razorpay_order_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    razorpay_payment_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    razorpay_signature: Mapped[str | None] = mapped_column(String(512), nullable=True)

    # Pricing (in paise — ₹1 = 100 paise)
    subtotal: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    total: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    # Customer info snapshot
    customer_name: Mapped[str] = mapped_column(String(255), nullable=False)
    customer_phone: Mapped[str] = mapped_column(String(32), nullable=False)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Timestamps for status transitions
    paid_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True,
    )
    confirmed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True,
    )
    ready_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True,
    )
    completed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True,
    )
    cancelled_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True,
    )

    # Relationships
    user: Mapped["User"] = relationship(backref="orders")
    items: Mapped[list["OrderItem"]] = relationship(
        back_populates="order",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )


class OrderItem(IDMixin, Base):
    __tablename__ = "order_items"
    __table_args__ = (
        Index("ix_order_items_order_id", "order_id"),
    )

    order_id: Mapped[int] = mapped_column(
        ForeignKey("orders.id", ondelete="CASCADE"),
        nullable=False,
    )
    product_id: Mapped[int | None] = mapped_column(
        ForeignKey("products.id", ondelete="SET NULL"),
        nullable=True,
    )
    variant_id: Mapped[int | None] = mapped_column(
        ForeignKey("variants.id", ondelete="SET NULL"),
        nullable=True,
    )

    # Snapshot fields (preserved even if product is deleted/edited)
    product_name: Mapped[str] = mapped_column(String(255), nullable=False)
    variant_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    unit_price: Mapped[int] = mapped_column(Integer, nullable=False)
    quantity: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    image_path: Mapped[str | None] = mapped_column(String(500), nullable=True)
    attributes: Mapped[dict | None] = mapped_column(JSON, nullable=True)

    # Relationships
    order: Mapped["Order"] = relationship(back_populates="items")
    product: Mapped["Product | None"] = relationship()
    variant: Mapped["Variant | None"] = relationship()
