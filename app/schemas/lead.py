from datetime import datetime

import html
from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.core.normalization import compact_whitespace, normalize_phone
from app.models.enums import LeadSource, LeadStatus


class LeadCreate(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    phone: str = Field(min_length=5, max_length=32)
    product_id: int | None = None
    variant_id: int | None = None
    message: str | None = Field(default=None, max_length=2000)
    source: LeadSource
    preferred_contact_time: str | None = Field(default=None, max_length=255)
    bot_check: str | None = None
    user_id: int | None = None

    @field_validator("name", "preferred_contact_time", "message")
    @classmethod
    def sanitize_and_normalize_text(cls, value: str | None) -> str | None:
        if not value:
            return value
        compacted = compact_whitespace(value)
        return html.escape(compacted) if compacted else None

    @field_validator("phone")
    @classmethod
    def normalize_phone_value(cls, value: str) -> str:
        normalized = normalize_phone(value)
        if len(normalized) < 5:
            raise ValueError("Phone number is too short.")
        return normalized


class LeadCreateResponse(BaseModel):
    id: int
    source: LeadSource
    status: LeadStatus
    whatsapp_url: str | None = None
    detail: str


class LeadRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    phone: str
    product_id: int | None = None
    variant_id: int | None = None
    message: str | None = None
    source: LeadSource
    status: LeadStatus
    preferred_contact_time: str | None = None


class AdminLeadRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    phone: str
    product_id: int | None = None
    product_name: str | None = None
    variant_id: int | None = None
    variant_name: str | None = None
    message: str | None = None
    source: LeadSource
    status: LeadStatus
    preferred_contact_time: str | None = None
    created_at: datetime
    updated_at: datetime
    contacted_at: datetime | None = None
    closed_at: datetime | None = None


class AdminLeadStatusUpdate(BaseModel):
    status: LeadStatus
