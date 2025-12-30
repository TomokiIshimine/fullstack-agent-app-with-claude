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
        super().__init__("このメールアドレスは既に使用されています", {"email": email})
        self.email = email


class UserNotFoundError(UserServiceError):
    """Raised when user is not found."""

    def __init__(self, user_id: int):
        super().__init__("ユーザーが見つかりません", {"user_id": user_id})
        self.user_id = user_id


class CannotDeleteAdminError(UserServiceError):
    """Raised when attempting to delete an admin user."""

    def __init__(self):
        super().__init__("管理者ユーザーは削除できません")


# === Conversation Exceptions ===


class ConversationServiceError(ServiceError):
    """Base exception for conversation service errors."""

    pass


class ConversationNotFoundError(ConversationServiceError):
    """Raised when conversation is not found."""

    def __init__(self, uuid: str):
        super().__init__("会話が見つかりません", {"uuid": uuid})
        self.uuid = uuid


class ConversationAccessDeniedError(ConversationServiceError):
    """Raised when user doesn't have access to conversation."""

    def __init__(self, uuid: str):
        super().__init__("この会話へのアクセス権限がありません", {"uuid": uuid})
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

    def __init__(self, message: str = "パスワードの変更に失敗しました"):
        super().__init__(message)


# === Database Exceptions ===


class DatabaseError(ServiceError):
    """Base exception for database-related errors."""

    pass


class DuplicateEntryError(DatabaseError):
    """Raised when a database unique constraint is violated (race condition)."""

    def __init__(self, message: str = "レコードが既に存在します", field: str | None = None):
        details = {"field": field} if field else {}
        super().__init__(message, details)
        self.field = field


class DatabaseConnectionError(DatabaseError):
    """Raised when database connection fails or times out."""

    def __init__(self, message: str = "データベース接続に失敗しました"):
        super().__init__(message)


# === LLM Provider Exceptions ===


class LLMProviderError(ServiceError):
    """Base exception for LLM provider errors."""

    pass


class ProviderNotFoundError(LLMProviderError):
    """Raised when specified provider is not supported."""

    def __init__(self, provider: str, supported: list[str] | None = None):
        supported_str = ", ".join(supported) if supported else "不明"
        super().__init__(
            f"サポートされていないLLMプロバイダー: '{provider}'. 対応プロバイダー: {supported_str}",
            {"provider": provider, "supported_providers": supported},
        )
        self.provider = provider
        self.supported_providers = supported


class ProviderConfigurationError(LLMProviderError):
    """Raised when provider configuration is invalid."""

    def __init__(self, message: str, field: str | None = None):
        details = {"field": field} if field else {}
        super().__init__(message, details)
        self.field = field


class ProviderAPIKeyError(LLMProviderError):
    """Raised when API key is missing or invalid."""

    def __init__(self, provider: str):
        super().__init__(
            f"{provider}のAPIキーが設定されていません",
            {"provider": provider},
        )
        self.provider = provider


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
    "DatabaseError",
    "DuplicateEntryError",
    "DatabaseConnectionError",
    "LLMProviderError",
    "ProviderNotFoundError",
    "ProviderConfigurationError",
    "ProviderAPIKeyError",
]
