"""User settings request/response schemas."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, field_validator


class UserSettingValidationError(ValueError):
    """Raised when user setting data validation fails."""

    pass


class UserSettingsResponse(BaseModel):
    """Schema for user settings GET response."""

    send_shortcut: Literal["enter", "ctrl_enter"] = "enter"


class UserSettingsUpdateRequest(BaseModel):
    """Schema for updating user settings."""

    send_shortcut: Literal["enter", "ctrl_enter"]

    @field_validator("send_shortcut")
    @classmethod
    def validate_send_shortcut(cls, v: str) -> str:
        """Validate send_shortcut value."""
        if v not in ("enter", "ctrl_enter"):
            raise UserSettingValidationError("send_shortcut must be 'enter' or 'ctrl_enter'")
        return v


class UserSettingsUpdateResponse(BaseModel):
    """Schema for user settings PATCH response."""

    message: str
    send_shortcut: Literal["enter", "ctrl_enter"]


__all__ = [
    "UserSettingValidationError",
    "UserSettingsResponse",
    "UserSettingsUpdateRequest",
    "UserSettingsUpdateResponse",
]
