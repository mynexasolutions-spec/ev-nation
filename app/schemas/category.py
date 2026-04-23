from pydantic import BaseModel, ConfigDict, Field, field_validator
from app.core.normalization import compact_whitespace


class CategoryBase(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    description: str | None = Field(default=None, max_length=500)
    sort_order: int = Field(default=0, ge=0)
    is_active: bool = True

    @field_validator("name", "description")
    @classmethod
    def normalize_text(cls, value: str | None) -> str | None:
        return compact_whitespace(value)


class CategoryRead(CategoryBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    slug: str


class CategoryCreate(CategoryBase):
    slug: str | None = Field(default=None, max_length=255)

    @field_validator("slug")
    @classmethod
    def normalize_text_slug(cls, value: str | None) -> str | None:
        return compact_whitespace(value)


class CategoryUpdate(CategoryBase):
    pass
