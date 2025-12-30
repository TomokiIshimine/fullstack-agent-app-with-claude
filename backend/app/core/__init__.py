"""Core module for shared application components."""

from app.core.exceptions import (
    AuthServiceError,
    CannotDeleteAdminError,
    ConversationAccessDeniedError,
    ConversationNotFoundError,
    ConversationServiceError,
    InvalidCredentialsError,
    InvalidPasswordError,
    InvalidRefreshTokenError,
    PasswordChangeFailedError,
    PasswordServiceError,
    ServiceError,
    UserAlreadyExistsError,
    UserNotFoundError,
    UserServiceError,
)

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
