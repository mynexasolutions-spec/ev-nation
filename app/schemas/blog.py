from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, EmailStr, field_validator


class BlogCategoryCreate(BaseModel):
    name: str
    slug: str


class BlogCategoryRead(BaseModel):
    id: int
    name: str
    slug: str

    model_config = {"from_attributes": True}


class BlogPostCreate(BaseModel):
    title: str
    slug: str
    short_description: str | None = None
    content: str | None = None
    author: str | None = "EV Nation Team"
    read_time: int | None = None
    category_id: int | None = None
    is_featured: bool = False
    is_published: bool = False


class BlogPostUpdate(BlogPostCreate):
    pass


class BlogPostRead(BaseModel):
    id: int
    title: str
    slug: str
    primary_image: str | None
    short_description: str | None
    content: str | None
    author: str | None
    read_time: int | None
    category_id: int | None
    is_featured: bool
    is_published: bool
    created_at: datetime
    updated_at: datetime
    category: BlogCategoryRead | None = None

    model_config = {"from_attributes": True}


class BlogSubscriberCreate(BaseModel):
    email: EmailStr

    @field_validator("email")
    @classmethod
    def lowercase_email(cls, v: str) -> str:
        return v.lower().strip()


class BlogSubscriberRead(BaseModel):
    id: int
    email: str
    is_active: bool
    created_at: datetime

    model_config = {"from_attributes": True}
