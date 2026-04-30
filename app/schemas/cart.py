from pydantic import BaseModel, ConfigDict, Field


class CartItemCreate(BaseModel):
    product_id: int
    variant_id: int | None = None
    quantity: int = Field(default=1, ge=1, le=10)
    attributes: dict | None = None


class CartItemUpdate(BaseModel):
    quantity: int = Field(ge=1, le=10)


class CartSyncItem(BaseModel):
    """A single item from the guest's localStorage cart."""
    product_id: int
    variant_id: int | None = None
    quantity: int = Field(default=1, ge=1, le=10)
    attributes: dict | None = None


class CartItemRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    product_id: int
    variant_id: int | None = None
    quantity: int
    attributes: dict | None = None
    # Enriched fields (filled by the service)
    product_name: str = ""
    product_slug: str = ""
    variant_name: str | None = None
    unit_price: int = 0
    image_path: str | None = None
    is_available: bool = True


class CartSummary(BaseModel):
    items: list[CartItemRead] = Field(default_factory=list)
    item_count: int = 0
    subtotal: int = 0  # in paise
