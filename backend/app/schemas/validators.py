"""Common validation functions for schemas."""

from __future__ import annotations

import re
from typing import Type

# Password validation constants
MIN_PASSWORD_LENGTH = 8

# Message validation constants
MAX_MESSAGE_LENGTH = 32000


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


__all__ = [
    "MIN_PASSWORD_LENGTH",
    "MAX_MESSAGE_LENGTH",
    "PasswordValidationError",
    "validate_password",
    "validate_message_content",
]
