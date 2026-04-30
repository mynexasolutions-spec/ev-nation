from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class OrderItemRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    product_id: int | None = None
    variant_id: int | None = None
    product_name: str
    variant_name: str | None = None
    unit_price: int
    quantity: int
    image_path: str | None = None
    attributes: dict | None = None


class OrderCreate(BaseModel):
    customer_name: str = Field(min_length=1, max_length=255)
    customer_phone: str = Field(min_length=10, max_length=32)
    notes: str | None = Field(default=None, max_length=1000)


class OrderRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    order_number: str
    status: str
    payment_status: str
    subtotal: int
    total: int
    customer_name: str
    customer_phone: str
    notes: str | None = None
    razorpay_order_id: str | None = None
    items: list[OrderItemRead] = Field(default_factory=list)
    created_at: datetime
    paid_at: datetime | None = None
    confirmed_at: datetime | None = None
    ready_at: datetime | None = None
    completed_at: datetime | None = None
    cancelled_at: datetime | None = None


class OrderListItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    order_number: str
    status: str
    payment_status: str
    total: int
    item_count: int = 0
    created_at: datetime


class PaymentInitResponse(BaseModel):
    razorpay_order_id: str
    razorpay_key_id: str
    amount: int
    currency: str = "INR"
    order_number: str
    customer_name: str
    customer_phone: str


class PaymentVerify(BaseModel):
    razorpay_order_id: str
    razorpay_payment_id: str
    razorpay_signature: str


class OrderStatusUpdate(BaseModel):
    status: str
