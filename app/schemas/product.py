from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.core.normalization import compact_whitespace, normalize_hex_color, normalize_slug, normalize_spec_key


class ProductImageBase(BaseModel):
    image_path: str = Field(min_length=1, max_length=500)
    alt_text: str | None = Field(default=None, max_length=255)
    is_primary: bool = False
    sort_order: int = Field(default=0, ge=0)

    @field_validator("image_path", "alt_text")
    @classmethod
    def normalize_text(cls, value: str | None) -> str | None:
        return compact_whitespace(value)


class ProductImageRead(ProductImageBase):
    model_config = ConfigDict(from_attributes=True)

    id: int


class ProductImageWrite(ProductImageBase):
    id: int | None = None


class VariantBase(BaseModel):
    color_name: str = Field(min_length=1, max_length=100)
    color_code: str | None = None
    image_path: str | None = Field(default=None, max_length=500)
    sort_order: int = Field(default=0, ge=0)
    is_active: bool = True

    @field_validator("color_name", "image_path")
    @classmethod
    def normalize_text(cls, value: str | None) -> str | None:
        return compact_whitespace(value)

    @field_validator("color_code")
    @classmethod
    def validate_hex_color(cls, value: str | None) -> str | None:
        return normalize_hex_color(value)


class VariantRead(VariantBase):
    model_config = ConfigDict(from_attributes=True)

    id: int


class VariantWrite(VariantBase):
    id: int | None = None


class ProductSpecBase(BaseModel):
    weight: str | None = Field(default=None, max_length=100)
    speed: str | None = Field(default=None, max_length=100)
    range: str | None = Field(default=None, max_length=100)
    rated_power: str | None = Field(default=None, max_length=100)
    peak_power: str | None = Field(default=None, max_length=100)
    carrying_capacity: str | None = Field(default=None, max_length=100)
    motor: str | None = Field(default=None, max_length=255)
    battery_type: str | None = Field(default=None, max_length=255)
    charging_time: str | None = Field(default=None, max_length=100)
    body: str | None = Field(default=None, max_length=255)
    ground_clearance: str | None = Field(default=None, max_length=100)
    seat_height: str | None = Field(default=None, max_length=100)
    wheel_type: str | None = Field(default=None, max_length=100)
    brake_system: str | None = Field(default=None, max_length=255)
    tyre_size: str | None = Field(default=None, max_length=100)

    @field_validator(
        "weight",
        "speed",
        "range",
        "rated_power",
        "peak_power",
        "carrying_capacity",
        "motor",
        "battery_type",
        "charging_time",
        "body",
        "ground_clearance",
        "seat_height",
        "wheel_type",
        "brake_system",
        "tyre_size",
    )
    @classmethod
    def normalize_text(cls, value: str | None) -> str | None:
        return compact_whitespace(value)


class ProductSpecRead(ProductSpecBase):
    model_config = ConfigDict(from_attributes=True)

    id: int


class ProductSpecWrite(ProductSpecBase):
    id: int | None = None


class BatteryOptionBase(BaseModel):
    capacity: str = Field(min_length=1, max_length=100)
    range: str = Field(min_length=1, max_length=100)
    sort_order: int = Field(default=0, ge=0)

    @field_validator("capacity", "range")
    @classmethod
    def normalize_text(cls, value: str) -> str:
        normalized = compact_whitespace(value)
        if normalized is None:
            raise ValueError("Battery option fields cannot be empty.")
        return normalized


class BatteryOptionRead(BatteryOptionBase):
    model_config = ConfigDict(from_attributes=True)

    id: int


class BatteryOptionWrite(BatteryOptionBase):
    id: int | None = None


class ExtraSpecBase(BaseModel):
    key: str = Field(min_length=1, max_length=100)
    label: str = Field(min_length=1, max_length=120)
    value: str = Field(min_length=1, max_length=500)
    sort_order: int = Field(default=0, ge=0)

    @field_validator("key")
    @classmethod
    def normalize_key(cls, value: str) -> str:
        normalized = normalize_spec_key(value)
        if not normalized:
            raise ValueError("Extra spec key cannot be empty.")
        return normalized

    @field_validator("label", "value")
    @classmethod
    def normalize_text(cls, value: str) -> str:
        normalized = compact_whitespace(value)
        if normalized is None:
            raise ValueError("Extra spec fields cannot be empty.")
        return normalized


class ExtraSpecRead(ExtraSpecBase):
    model_config = ConfigDict(from_attributes=True)

    id: int


class ExtraSpecWrite(ExtraSpecBase):
    id: int | None = None


class ProductBase(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    slug: str | None = Field(default=None, max_length=255)
    tagline: str | None = Field(default=None, max_length=255)
    short_description: str | None = None
    description: str | None = None
    is_active: bool = True
    sort_order: int = Field(default=0, ge=0)

    @field_validator("name", "tagline", "short_description", "description")
    @classmethod
    def normalize_text(cls, value: str | None) -> str | None:
        return compact_whitespace(value)

    @field_validator("slug")
    @classmethod
    def normalize_slug_value(cls, value: str | None) -> str | None:
        if value is None:
            return None
        normalized = normalize_slug(value)
        if not normalized:
            raise ValueError("Slug cannot be empty.")
        return normalized


class ProductListItem(BaseModel):
    id: int
    name: str
    slug: str
    tagline: str | None = None
    short_description: str | None = None
    sort_order: int
    primary_image: ProductImageRead | None = None
    variants: list[VariantRead] = Field(default_factory=list)


class ProductDetailRead(BaseModel):
    id: int
    name: str
    slug: str
    tagline: str | None = None
    short_description: str | None = None
    description: str | None = None
    sort_order: int
    images: list[ProductImageRead] = Field(default_factory=list)
    variants: list[VariantRead] = Field(default_factory=list)
    spec: ProductSpecRead | None = None
    battery_options: list[BatteryOptionRead] = Field(default_factory=list)
    extra_specs: list[ExtraSpecRead] = Field(default_factory=list)


class AdminProductCreate(ProductBase):
    images: list[ProductImageWrite] = Field(default_factory=list)
    variants: list[VariantWrite] = Field(default_factory=list)
    spec: ProductSpecWrite | None = None
    battery_options: list[BatteryOptionWrite] = Field(default_factory=list)
    extra_specs: list[ExtraSpecWrite] = Field(default_factory=list)


class AdminProductUpdate(BaseModel):
    name: str | None = Field(default=None, max_length=255)
    slug: str | None = Field(default=None, max_length=255)
    tagline: str | None = Field(default=None, max_length=255)
    short_description: str | None = None
    description: str | None = None
    is_active: bool | None = None
    sort_order: int | None = Field(default=None, ge=0)
    images: list[ProductImageWrite] | None = None
    variants: list[VariantWrite] | None = None
    spec: ProductSpecWrite | None = None
    battery_options: list[BatteryOptionWrite] | None = None
    extra_specs: list[ExtraSpecWrite] | None = None

    @field_validator("name", "tagline", "short_description", "description")
    @classmethod
    def normalize_text(cls, value: str | None) -> str | None:
        return compact_whitespace(value)

    @field_validator("slug")
    @classmethod
    def normalize_slug_value(cls, value: str | None) -> str | None:
        if value is None:
            return None
        normalized = normalize_slug(value)
        if not normalized:
            raise ValueError("Slug cannot be empty.")
        return normalized


class AdminProductListItem(ProductListItem):
    is_active: bool


class AdminProductDetailRead(ProductDetailRead):
    is_active: bool
