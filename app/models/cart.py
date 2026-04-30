from __future__ import annotations

from sqlalchemy import ForeignKey, Index, Integer, UniqueConstraint, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base_class import Base
from app.models.mixins import IDMixin, TimestampMixin


class CartItem(IDMixin, TimestampMixin, Base):
    __tablename__ = "cart_items"
    __table_args__ = (
        UniqueConstraint(
            "user_id", "product_id", "variant_id",
            name="uq_cart_items_user_product_variant",
        ),
        Index("ix_cart_items_user_id", "user_id"),
    )

    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    product_id: Mapped[int] = mapped_column(
        ForeignKey("products.id", ondelete="CASCADE"),
        nullable=False,
    )
    variant_id: Mapped[int | None] = mapped_column(
        ForeignKey("variants.id", ondelete="SET NULL"),
        nullable=True,
    )
    quantity: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=1,
        server_default="1",
    )
    attributes: Mapped[dict | None] = mapped_column(JSON, nullable=True)

    user: Mapped["User"] = relationship(backref="cart_items")
    product: Mapped["Product"] = relationship()
    variant: Mapped["Variant | None"] = relationship()
