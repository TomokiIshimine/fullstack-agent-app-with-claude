"""Route-level helpers for dependency injection and request validation."""

from __future__ import annotations

import logging
from functools import wraps
from typing import Any, Callable, TypeVar

from flask import g, request
from pydantic import BaseModel, ValidationError
from sqlalchemy.exc import IntegrityError, OperationalError, SQLAlchemyError
from werkzeug.exceptions import BadRequest, Conflict, Forbidden, HTTPException, InternalServerError, NotFound, ServiceUnavailable, Unauthorized

from app.core.exceptions import (
    AuthServiceError,
    CannotDeleteAdminError,
    ConversationAccessDeniedError,
    ConversationNotFoundError,
    ConversationServiceError,
    DatabaseConnectionError,
    DuplicateEntryError,
    InvalidCredentialsError,
    InvalidPasswordError,
    InvalidRefreshTokenError,
    LLMProviderError,
    PasswordChangeFailedError,
    PasswordServiceError,
    ProviderAPIKeyError,
    ProviderConfigurationError,
    ProviderNotFoundError,
    UserAlreadyExistsError,
    UserNotFoundError,
    UserServiceError,
)
from app.database import get_session
from app.providers import BaseLLMProvider, create_provider
from app.schemas.password import PasswordValidationError
from app.schemas.user import UserValidationError
from app.schemas.validators import InvalidUUIDError, validate_uuid
from app.services.admin_conversation_service import AdminConversationService
from app.services.admin_dashboard_service import AdminDashboardService
from app.services.agent_service import AgentService
from app.services.auth_service import AuthService
from app.services.conversation_service import ConversationService
from app.services.password_service import PasswordService
from app.services.user_service import UserService

logger = logging.getLogger(__name__)

# Type alias for error mapping: exception class -> HTTP exception class
ErrorMapping = dict[type[Exception], type[HTTPException]]

SchemaType = TypeVar("SchemaType", bound=BaseModel)
RouteCallable = TypeVar("RouteCallable", bound=Callable[..., Any])


def _handle_sqlalchemy_error(exc: SQLAlchemyError) -> None:
    """Translate SQLAlchemy exceptions to HTTP exceptions.

    Args:
        exc: The SQLAlchemy exception to handle

    Raises:
        Conflict: For unique constraint violations (IntegrityError)
        ServiceUnavailable: For connection failures (OperationalError)
        InternalServerError: For other database errors
    """
    if isinstance(exc, IntegrityError):
        error_msg = str(exc.orig) if hasattr(exc, "orig") else str(exc)
        field = None
        if "Duplicate entry" in error_msg and "for key" in error_msg:
            key_part = error_msg.split("for key")[-1].strip(" '\"")
            field = key_part.split(".")[-1] if "." in key_part else key_part
        elif "UNIQUE constraint failed" in error_msg:
            field = error_msg.split(":")[-1].strip().split(".")[-1]
        logger.warning(f"Database integrity error: {error_msg}", extra={"field": field})
        raise Conflict(description=str(DuplicateEntryError(field=field))) from exc
    elif isinstance(exc, OperationalError):
        logger.error(f"Database connection error: {exc}", exc_info=True)
        raise ServiceUnavailable(description=str(DatabaseConnectionError())) from exc
    else:
        logger.error(f"Unexpected database error: {exc}", exc_info=True)
        raise InternalServerError(description="データベースエラーが発生しました") from exc


def _create_service_decorator(
    service_getter: Callable[[], Any],
    service_kwarg: str,
    error_mapping: ErrorMapping,
    fallback_error_class: type[Exception],
    service_name: str,
) -> Callable[[RouteCallable], RouteCallable]:
    """Create a service injection decorator with error handling.

    Factory function that generates decorators for injecting services into
    route handlers while translating domain exceptions to HTTP exceptions.

    Args:
        service_getter: Function that returns the service instance.
        service_kwarg: Name of the keyword argument to inject the service as.
        error_mapping: Dict mapping domain exception classes to HTTP exception classes.
        fallback_error_class: Service error class to catch as fallback (logs and raises 500).
        service_name: Human-readable service name for logging.

    Returns:
        A decorator function that can be applied to route handlers.

    Example:
        with_auth_service = _create_service_decorator(
            service_getter=get_auth_service,
            service_kwarg="auth_service",
            error_mapping={
                InvalidCredentialsError: Unauthorized,
                InvalidRefreshTokenError: Unauthorized,
            },
            fallback_error_class=AuthServiceError,
            service_name="auth",
        )
    """

    def decorator(func: RouteCallable) -> RouteCallable:
        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any):
            service = service_getter()
            try:
                return func(*args, **{service_kwarg: service}, **kwargs)
            except tuple(error_mapping.keys()) as exc:
                http_exc_class = error_mapping[type(exc)]
                raise http_exc_class(description=str(exc)) from exc
            except HTTPException:
                # Let HTTP exceptions (BadRequest, NotFound, etc.) pass through
                raise
            except SQLAlchemyError as exc:
                _handle_sqlalchemy_error(exc)
            except Exception as exc:
                if isinstance(exc, fallback_error_class):
                    logger.error(f"{service_name.capitalize()} service error", exc_info=True)
                    raise InternalServerError(description=str(exc)) from exc
                # pragma: no cover - unexpected error path
                logger.error(f"Unexpected error in {service_name} route", exc_info=True)
                raise

        return wrapper  # type: ignore[return-value]

    return decorator


# === Service Factories ===


def get_llm_provider() -> BaseLLMProvider:
    """Return request-scoped LLM provider instance.

    Creates a single LLM provider per request and caches it in Flask's g object.
    This enables consistent provider usage across a request lifecycle.

    Returns:
        BaseLLMProvider instance configured from environment variables.

    Raises:
        BadRequest: If provider configuration is invalid or provider not found.
        InternalServerError: If API key is missing or other provider errors.
    """
    if provider := g.get("llm_provider"):
        return provider

    try:
        provider = create_provider()
    except ProviderNotFoundError as exc:
        logger.error(f"LLM provider not found: {exc}")
        raise BadRequest(description=str(exc)) from exc
    except ProviderConfigurationError as exc:
        logger.error(f"LLM provider configuration error: {exc}")
        raise BadRequest(description=str(exc)) from exc
    except ProviderAPIKeyError as exc:
        logger.error(f"LLM provider API key error: {exc}")
        raise InternalServerError(description=str(exc)) from exc
    except LLMProviderError as exc:
        logger.error(f"LLM provider error: {exc}")
        raise InternalServerError(description=str(exc)) from exc

    g.llm_provider = provider
    return provider


def get_agent_service() -> AgentService:
    """Return request-scoped AgentService instance.

    Creates a single AgentService per request, using the shared LLM provider.

    Returns:
        AgentService instance with LLM provider and default tools.
    """
    if service := g.get("agent_service"):
        return service

    provider = get_llm_provider()
    service = AgentService(provider=provider)
    g.agent_service = service
    return service


def get_auth_service() -> AuthService:
    """Return request-scoped AuthService instance."""
    if service := g.get("auth_service"):
        return service

    session = get_session()
    service = AuthService(session)
    g.auth_service = service
    return service


def get_conversation_service() -> ConversationService:
    """Return request-scoped ConversationService instance."""
    if service := g.get("conversation_service"):
        return service

    session = get_session()
    service = ConversationService(session)
    g.conversation_service = service
    return service


def get_password_service() -> PasswordService:
    """Return request-scoped PasswordService instance."""
    if service := g.get("password_service"):
        return service

    session = get_session()
    service = PasswordService(session)
    g.password_service = service
    return service


def get_user_service() -> UserService:
    """Return request-scoped UserService instance."""
    if service := g.get("user_service"):
        return service

    session = get_session()
    service = UserService(session)
    g.user_service = service
    return service


def get_admin_conversation_service() -> AdminConversationService:
    """Return request-scoped AdminConversationService instance."""
    if service := g.get("admin_conversation_service"):
        return service

    session = get_session()
    service = AdminConversationService(session)
    g.admin_conversation_service = service
    return service


def get_admin_dashboard_service() -> AdminDashboardService:
    """Return request-scoped AdminDashboardService instance."""
    if service := g.get("admin_dashboard_service"):
        return service

    session = get_session()
    service = AdminDashboardService(session)
    g.admin_dashboard_service = service
    return service


# === Service Injection Decorators ===

# Error mappings for each service (domain exception -> HTTP exception)
_AUTH_ERROR_MAPPING: ErrorMapping = {
    InvalidCredentialsError: Unauthorized,
    InvalidRefreshTokenError: Unauthorized,
}

_CONVERSATION_ERROR_MAPPING: ErrorMapping = {
    ConversationNotFoundError: NotFound,
    ConversationAccessDeniedError: Forbidden,
}

_PASSWORD_ERROR_MAPPING: ErrorMapping = {
    InvalidPasswordError: Unauthorized,
    PasswordChangeFailedError: InternalServerError,
}

_USER_ERROR_MAPPING: ErrorMapping = {
    UserAlreadyExistsError: Conflict,
    UserNotFoundError: NotFound,
    CannotDeleteAdminError: Forbidden,
}

with_auth_service: Callable[[RouteCallable], RouteCallable] = _create_service_decorator(
    service_getter=get_auth_service,
    service_kwarg="auth_service",
    error_mapping=_AUTH_ERROR_MAPPING,
    fallback_error_class=AuthServiceError,
    service_name="auth",
)
with_auth_service.__doc__ = "Inject AuthService and translate domain errors into HTTP responses."

with_conversation_service: Callable[[RouteCallable], RouteCallable] = _create_service_decorator(
    service_getter=get_conversation_service,
    service_kwarg="conversation_service",
    error_mapping=_CONVERSATION_ERROR_MAPPING,
    fallback_error_class=ConversationServiceError,
    service_name="conversation",
)
with_conversation_service.__doc__ = "Inject ConversationService and translate domain errors into HTTP responses."

with_password_service: Callable[[RouteCallable], RouteCallable] = _create_service_decorator(
    service_getter=get_password_service,
    service_kwarg="password_service",
    error_mapping=_PASSWORD_ERROR_MAPPING,
    fallback_error_class=PasswordServiceError,
    service_name="password",
)
with_password_service.__doc__ = "Inject PasswordService and translate domain errors into HTTP responses."

with_user_service: Callable[[RouteCallable], RouteCallable] = _create_service_decorator(
    service_getter=get_user_service,
    service_kwarg="user_service",
    error_mapping=_USER_ERROR_MAPPING,
    fallback_error_class=UserServiceError,
    service_name="user",
)
with_user_service.__doc__ = "Inject UserService and translate domain errors into HTTP responses."

_ADMIN_CONVERSATION_ERROR_MAPPING: ErrorMapping = {
    ConversationNotFoundError: NotFound,
}

with_admin_conversation_service: Callable[[RouteCallable], RouteCallable] = _create_service_decorator(
    service_getter=get_admin_conversation_service,
    service_kwarg="admin_conversation_service",
    error_mapping=_ADMIN_CONVERSATION_ERROR_MAPPING,
    fallback_error_class=ConversationServiceError,
    service_name="admin_conversation",
)
with_admin_conversation_service.__doc__ = "Inject AdminConversationService and translate domain errors into HTTP responses."

# Admin Dashboard has no specific domain errors, just use empty mapping
_ADMIN_DASHBOARD_ERROR_MAPPING: ErrorMapping = {}

with_admin_dashboard_service: Callable[[RouteCallable], RouteCallable] = _create_service_decorator(
    service_getter=get_admin_dashboard_service,
    service_kwarg="admin_dashboard_service",
    error_mapping=_ADMIN_DASHBOARD_ERROR_MAPPING,
    fallback_error_class=Exception,
    service_name="admin_dashboard",
)
with_admin_dashboard_service.__doc__ = "Inject AdminDashboardService and translate domain errors into HTTP responses."


# === Request Validation Decorator ===


def validate_request_body(schema: type[SchemaType]) -> Callable[[RouteCallable], RouteCallable]:
    """Validate JSON request body with given schema and pass it to the route."""

    def decorator(func: RouteCallable) -> RouteCallable:
        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any):
            payload = request.get_json()
            if not payload:
                logger.warning("Validation failed: request body is required", extra={"path": request.path})
                raise BadRequest(description="Request body is required")

            try:
                data = schema.model_validate(payload)
            except ValidationError as exc:
                messages = ", ".join(err.get("msg", "Invalid value") for err in exc.errors())
                logger.warning("Validation failed for request body", extra={"path": request.path, "messages": messages})
                raise BadRequest(description=f"Validation error: {messages}") from exc
            except (UserValidationError, PasswordValidationError) as exc:
                logger.warning("Domain validation failed", extra={"path": request.path, "message": str(exc)})
                raise BadRequest(description=str(exc)) from exc

            return func(*args, data=data, **kwargs)

        return wrapper  # type: ignore[return-value]

    return decorator


def validate_uuid_param(param_name: str = "uuid") -> Callable[[RouteCallable], RouteCallable]:
    """Validate UUID path parameter format before processing.

    This decorator validates that a UUID path parameter is properly formatted
    (UUID v4 format) before the route handler processes it. This prevents
    malformed UUIDs from reaching the database layer.

    Args:
        param_name: Name of the path parameter to validate (default: "uuid").

    Returns:
        A decorator that validates the UUID parameter.

    Example:
        @conversation_bp.get("/<uuid>")
        @require_auth
        @validate_uuid_param("uuid")
        def get_conversation(uuid: str):
            ...
    """

    def decorator(func: RouteCallable) -> RouteCallable:
        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any):
            uuid_value = kwargs.get(param_name)
            if uuid_value is None:
                logger.warning(
                    f"UUID validation failed: {param_name} not found",
                    extra={"path": request.path},
                )
                raise BadRequest(description=f"Path parameter '{param_name}' is required")

            try:
                validated_uuid = validate_uuid(uuid_value, field_name="Conversation ID")
                kwargs[param_name] = validated_uuid
            except InvalidUUIDError as exc:
                logger.warning(
                    f"UUID validation failed: {uuid_value}",
                    extra={"path": request.path, "param": param_name},
                )
                raise BadRequest(description=str(exc)) from exc

            return func(*args, **kwargs)

        return wrapper  # type: ignore[return-value]

    return decorator


__all__ = [
    "get_admin_conversation_service",
    "get_admin_dashboard_service",
    "get_agent_service",
    "get_auth_service",
    "get_conversation_service",
    "get_llm_provider",
    "get_password_service",
    "get_user_service",
    "with_admin_conversation_service",
    "with_admin_dashboard_service",
    "with_auth_service",
    "with_conversation_service",
    "with_password_service",
    "with_user_service",
    "validate_request_body",
    "validate_uuid_param",
]
