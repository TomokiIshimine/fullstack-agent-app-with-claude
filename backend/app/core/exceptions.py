"""Centralized exception definitions for domain services."""

from __future__ import annotations


class ServiceError(Exception):
    """Base exception for all service layer errors.

    Attributes:
        message: Human-readable error message
        details: Optional additional context
    """

    def __init__(self, message: str, details: dict | None = None):
        super().__init__(message)
        self.message = message
        self.details = details or {}


# === Authentication Exceptions ===


class AuthServiceError(ServiceError):
    """Base exception for authentication service errors."""

    pass


class InvalidCredentialsError(AuthServiceError):
    """Raised when login credentials are invalid."""

    def __init__(self, message: str = "メールアドレスまたはパスワードが間違っています"):
        super().__init__(message)


class InvalidRefreshTokenError(AuthServiceError):
    """Raised when refresh token is invalid or expired."""

    def __init__(self, message: str = "リフレッシュトークンが無効です"):
        super().__init__(message)


# === User Management Exceptions ===


class UserServiceError(ServiceError):
    """Base exception for user service errors."""

    pass


class UserAlreadyExistsError(UserServiceError):
    """Raised when attempting to create a user with duplicate email."""

    def __init__(self, email: str):
        super().__init__(f"User with email '{email}' already exists", {"email": email})
        self.email = email


class UserNotFoundError(UserServiceError):
    """Raised when user is not found."""

    def __init__(self, user_id: int):
        super().__init__(f"User with id {user_id} not found", {"user_id": user_id})
        self.user_id = user_id


class CannotDeleteAdminError(UserServiceError):
    """Raised when attempting to delete an admin user."""

    def __init__(self):
        super().__init__("Admin user cannot be deleted")


# === Conversation Exceptions ===


class ConversationServiceError(ServiceError):
    """Base exception for conversation service errors."""

    pass


class ConversationNotFoundError(ConversationServiceError):
    """Raised when conversation is not found."""

    def __init__(self, uuid: str):
        super().__init__("Conversation not found", {"uuid": uuid})
        self.uuid = uuid


class ConversationAccessDeniedError(ConversationServiceError):
    """Raised when user doesn't have access to conversation."""

    def __init__(self, uuid: str):
        super().__init__("Access denied", {"uuid": uuid})
        self.uuid = uuid


# === Password Exceptions ===


class PasswordServiceError(ServiceError):
    """Base exception for password service errors."""

    pass


class InvalidPasswordError(PasswordServiceError):
    """Raised when current password is incorrect."""

    def __init__(self):
        super().__init__("現在のパスワードが間違っています")


class PasswordChangeFailedError(PasswordServiceError):
    """Raised when password change operation fails."""

    def __init__(self, message: str = "Failed to change password"):
        super().__init__(message)


__all__ = [
    "ServiceError",
    "AuthServiceError",
    "InvalidCredentialsError",
    "InvalidRefreshTokenError",
    "UserServiceError",
    "UserAlreadyExistsError",
    "UserNotFoundError",
    "CannotDeleteAdminError",
    "ConversationServiceError",
    "ConversationNotFoundError",
    "ConversationAccessDeniedError",
    "PasswordServiceError",
    "InvalidPasswordError",
    "PasswordChangeFailedError",
]
