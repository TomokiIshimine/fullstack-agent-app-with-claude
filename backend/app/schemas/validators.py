"""Common validation functions for schemas."""

from __future__ import annotations

import re
import uuid as uuid_module
from typing import Type

# Import validation constants from centralized location
# Re-exported for backward compatibility
from app.constants.validation import MAX_MESSAGE_LENGTH, MIN_PASSWORD_LENGTH

# UUID v4 pattern for validation (strict format check)
UUID_V4_PATTERN = re.compile(
    r"^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$",
    re.IGNORECASE,
)


class InvalidUUIDError(ValueError):
    """Raised when UUID validation fails."""

    pass


class PasswordValidationError(ValueError):
    """Raised when password validation fails.

    This error is raised from password-related schemas (e.g., PasswordChangeRequest)
    to maintain backward compatibility with existing error handling.
    """

    pass


def validate_password(
    password: str,
    *,
    exception_class: Type[Exception] = ValueError,
) -> str:
    """Validate password meets security requirements.

    Args:
        password: The password to validate.
        exception_class: The exception class to raise on validation failure.
            Defaults to ValueError.

    Returns:
        The validated password (unchanged).

    Raises:
        ValueError or exception_class: If password validation fails.
    """
    if not password or len(password) < MIN_PASSWORD_LENGTH:
        raise exception_class(f"Password must be at least {MIN_PASSWORD_LENGTH} characters long")

    # Check for alphanumeric characters
    if not re.search(r"[a-zA-Z]", password) or not re.search(r"[0-9]", password):
        raise exception_class("Password must contain both letters and numbers")

    return password


def validate_message_content(
    content: str,
    field_name: str = "Content",
) -> str:
    """Validate message content.

    Args:
        content: The message content to validate.
        field_name: The name of the field for error messages (e.g., "Message", "Content").

    Returns:
        The validated and trimmed content.

    Raises:
        ValueError: If content validation fails.
    """
    if not content or not content.strip():
        raise ValueError(f"{field_name} is required")

    if len(content) > MAX_MESSAGE_LENGTH:
        raise ValueError(f"{field_name} must be at most {MAX_MESSAGE_LENGTH} characters")

    return content.strip()


def validate_uuid(
    value: str,
    field_name: str = "UUID",
) -> str:
    """Validate UUID format (v4).

    Validates that the given string is a properly formatted UUID v4.
    This prevents malformed UUIDs from reaching the database layer.

    Args:
        value: The UUID string to validate.
        field_name: The name of the field for error messages.

    Returns:
        The validated UUID string (lowercase, normalized).

    Raises:
        InvalidUUIDError: If UUID format is invalid.
    """
    if not value:
        raise InvalidUUIDError(f"{field_name} is required")

    # Check length first (quick check)
    if len(value) != 36:
        raise InvalidUUIDError(f"Invalid {field_name} format")

    # Validate UUID v4 format with regex
    if not UUID_V4_PATTERN.match(value):
        raise InvalidUUIDError(f"Invalid {field_name} format")

    # Additional validation using uuid module
    try:
        parsed = uuid_module.UUID(value, version=4)
        return str(parsed)
    except ValueError as exc:
        raise InvalidUUIDError(f"Invalid {field_name} format") from exc


__all__ = [
    "MIN_PASSWORD_LENGTH",
    "MAX_MESSAGE_LENGTH",
    "InvalidUUIDError",
    "PasswordValidationError",
    "validate_password",
    "validate_message_content",
    "validate_uuid",
]
