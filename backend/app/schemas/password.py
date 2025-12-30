"""Password management request/response schemas."""

from __future__ import annotations

from pydantic import BaseModel, field_validator

from app.schemas.validators import PasswordValidationError, validate_password


class PasswordChangeRequest(BaseModel):
    """Schema for changing password."""

    current_password: str
    new_password: str

    @field_validator("current_password")
    @classmethod
    def validate_current_password(cls, v: str) -> str:
        """Validate current password is not empty."""
        if not v:
            raise PasswordValidationError("Current password is required")
        return v

    @field_validator("new_password")
    @classmethod
    def validate_new_password(cls, v: str) -> str:
        """Validate new password format."""
        return validate_password(v, exception_class=PasswordValidationError)


class PasswordChangeResponse(BaseModel):
    """Schema for password change response."""

    message: str


__all__ = [
    "PasswordChangeRequest",
    "PasswordChangeResponse",
    "PasswordValidationError",
]
