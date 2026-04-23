from __future__ import annotations

from sqlalchemy import Boolean, ForeignKey, Index, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import expression

from app.db.base_class import Base
from app.models.category import Category
from app.models.mixins import IDMixin, TimestampMixin


class Product(IDMixin, TimestampMixin, Base):
    __tablename__ = "products"

    name: Mapped[str] = mapped_column(String(255), nullable=False)
    slug: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    tagline: Mapped[str | None] = mapped_column(String(255), nullable=True)
    short_description: Mapped[str | None] = mapped_column(Text, nullable=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    base_price: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        server_default="0",
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
        server_default=expression.true(),
        index=True,
    )
    sort_order: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        server_default="0",
        index=True,
    )
    category_id: Mapped[int | None] = mapped_column(
        ForeignKey("categories.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    category: Mapped[Category | None] = relationship(back_populates="products")

    images: Mapped[list[ProductImage]] = relationship(
        back_populates="product",
        cascade="all, delete-orphan",
        passive_deletes=True,
        order_by="ProductImage.sort_order",
    )
    variants: Mapped[list[Variant]] = relationship(
        back_populates="product",
        cascade="all, delete-orphan",
        passive_deletes=True,
        order_by="Variant.sort_order",
    )
    spec: Mapped[ProductSpec | None] = relationship(
        back_populates="product",
        cascade="all, delete-orphan",
        passive_deletes=True,
        uselist=False,
    )
    battery_options: Mapped[list[BatteryOption]] = relationship(
        back_populates="product",
        cascade="all, delete-orphan",
        passive_deletes=True,
        order_by="BatteryOption.sort_order",
    )
    extra_specs: Mapped[list[ExtraSpec]] = relationship(
        back_populates="product",
        cascade="all, delete-orphan",
        passive_deletes=True,
        order_by="ExtraSpec.sort_order",
    )
    leads: Mapped[list["Lead"]] = relationship(back_populates="product")


class ProductImage(IDMixin, TimestampMixin, Base):
    __tablename__ = "product_images"
    __table_args__ = (
        Index("ix_product_images_product_id_sort_order", "product_id", "sort_order"),
    )

    product_id: Mapped[int] = mapped_column(
        ForeignKey("products.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    variant_id: Mapped[int | None] = mapped_column(
        ForeignKey("variants.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    image_path: Mapped[str] = mapped_column(String(500), nullable=False)
    alt_text: Mapped[str | None] = mapped_column(String(255), nullable=True)
    is_primary: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        server_default=expression.false(),
    )
    sort_order: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        server_default="0",
    )

    product: Mapped[Product] = relationship(back_populates="images")
    variant: Mapped[Variant | None] = relationship(back_populates="images")


class Variant(IDMixin, TimestampMixin, Base):
    __tablename__ = "variants"
    __table_args__ = (
        Index("ix_variants_product_id_sort_order", "product_id", "sort_order"),
        UniqueConstraint("product_id", "color_name", name="uq_variants_product_id_color_name"),
    )

    product_id: Mapped[int] = mapped_column(
        ForeignKey("products.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    color_name: Mapped[str] = mapped_column(String(100), nullable=False)
    color_code: Mapped[str | None] = mapped_column(String(7), nullable=True)
    image_path: Mapped[str | None] = mapped_column(String(500), nullable=True)
    sort_order: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        server_default="0",
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
        server_default=expression.true(),
    )

    product: Mapped[Product] = relationship(back_populates="variants")
    images: Mapped[list[ProductImage]] = relationship(
        back_populates="variant",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
    leads: Mapped[list["Lead"]] = relationship(back_populates="variant")


class ProductSpec(IDMixin, TimestampMixin, Base):
    __tablename__ = "product_specs"

    product_id: Mapped[int] = mapped_column(
        ForeignKey("products.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
        index=True,
    )
    weight: Mapped[str | None] = mapped_column(String(100), nullable=True)
    speed: Mapped[str | None] = mapped_column(String(100), nullable=True)
    range: Mapped[str | None] = mapped_column(String(100), nullable=True)
    rated_power: Mapped[str | None] = mapped_column(String(100), nullable=True)
    peak_power: Mapped[str | None] = mapped_column(String(100), nullable=True)
    carrying_capacity: Mapped[str | None] = mapped_column(String(100), nullable=True)
    motor: Mapped[str | None] = mapped_column(String(255), nullable=True)
    battery_type: Mapped[str | None] = mapped_column(String(255), nullable=True)
    charging_time: Mapped[str | None] = mapped_column(String(100), nullable=True)
    body: Mapped[str | None] = mapped_column(String(255), nullable=True)
    ground_clearance: Mapped[str | None] = mapped_column(String(100), nullable=True)
    seat_height: Mapped[str | None] = mapped_column(String(100), nullable=True)
    wheel_type: Mapped[str | None] = mapped_column(String(100), nullable=True)
    brake_system: Mapped[str | None] = mapped_column(String(255), nullable=True)
    tyre_size: Mapped[str | None] = mapped_column(String(100), nullable=True)

    product: Mapped[Product] = relationship(back_populates="spec")


class BatteryOption(IDMixin, TimestampMixin, Base):
    __tablename__ = "battery_options"
    __table_args__ = (
        Index("ix_battery_options_product_id_sort_order", "product_id", "sort_order"),
    )

    product_id: Mapped[int] = mapped_column(
        ForeignKey("products.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    capacity: Mapped[str] = mapped_column(String(100), nullable=False)
    range: Mapped[str] = mapped_column(String(100), nullable=False)
    sort_order: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        server_default="0",
    )

    product: Mapped[Product] = relationship(back_populates="battery_options")


class ExtraSpec(IDMixin, TimestampMixin, Base):
    __tablename__ = "extra_specs"
    __table_args__ = (
        Index("ix_extra_specs_product_id_sort_order", "product_id", "sort_order"),
        Index("ix_extra_specs_product_id_key", "product_id", "key"),
    )

    product_id: Mapped[int] = mapped_column(
        ForeignKey("products.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    key: Mapped[str] = mapped_column(String(100), nullable=False)
    label: Mapped[str] = mapped_column(String(120), nullable=False)
    value: Mapped[str] = mapped_column(String(500), nullable=False)
    sort_order: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        server_default="0",
    )

    product: Mapped[Product] = relationship(back_populates="extra_specs")
