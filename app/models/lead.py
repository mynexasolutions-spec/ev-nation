from __future__ import annotations

from datetime import datetime

from sqlalchemy import Enum, ForeignKey, Index, String, Text, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base_class import Base
from app.models.enums import LeadSource, LeadStatus
from app.models.mixins import IDMixin, TimestampMixin


class Lead(IDMixin, TimestampMixin, Base):
    __tablename__ = "leads"
    __table_args__ = (
        Index("ix_leads_created_at", "created_at"),
    )

    name: Mapped[str] = mapped_column(String(255), nullable=False)
    phone: Mapped[str] = mapped_column(String(32), nullable=False)
    product_id: Mapped[int | None] = mapped_column(
        ForeignKey("products.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    variant_id: Mapped[int | None] = mapped_column(
        ForeignKey("variants.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    message: Mapped[str | None] = mapped_column(Text, nullable=True)
    source: Mapped[LeadSource] = mapped_column(
        Enum(LeadSource, name="lead_source_enum"),
        nullable=False,
        index=True,
    )
    status: Mapped[LeadStatus] = mapped_column(
        Enum(LeadStatus, name="lead_status_enum"),
        nullable=False,
        default=LeadStatus.NEW,
        server_default=LeadStatus.NEW.value,
        index=True,
    )
    preferred_contact_time: Mapped[str | None] = mapped_column(String(255), nullable=True)
    contacted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    closed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    product: Mapped["Product | None"] = relationship(back_populates="leads")
    variant: Mapped["Variant | None"] = relationship(back_populates="leads")
