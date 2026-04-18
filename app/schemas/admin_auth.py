from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.core.normalization import compact_whitespace


class AdminLoginRequest(BaseModel):
    email: str = Field(min_length=3, max_length=255)
    password: str = Field(min_length=8, max_length=255)

    @field_validator("email")
    @classmethod
    def normalize_email(cls, value: str) -> str:
        normalized = compact_whitespace(value)
        if normalized is None or "@" not in normalized or normalized.startswith("@") or normalized.endswith("@"):
            raise ValueError("Email must look like a valid email address.")
        return normalized.lower()

    @field_validator("password")
    @classmethod
    def normalize_password(cls, value: str) -> str:
        normalized = compact_whitespace(value)
        if normalized is None:
            raise ValueError("Password cannot be empty.")
        return normalized


class AdminTokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class AdminUserRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    email: str
    full_name: str | None = None
    is_active: bool
    is_superuser: bool
