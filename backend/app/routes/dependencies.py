"""Route-level helpers for dependency injection and request validation."""

from __future__ import annotations

import logging
from functools import wraps
from typing import Any, Callable, TypeVar

from flask import g, request
from pydantic import BaseModel, ValidationError
from werkzeug.exceptions import BadRequest, Conflict, Forbidden, InternalServerError, NotFound, Unauthorized

from app.core.exceptions import (  # Auth exceptions; Conversation exceptions; Password exceptions; User exceptions
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
    UserAlreadyExistsError,
    UserNotFoundError,
    UserServiceError,
)
from app.database import get_session
from app.schemas.password import PasswordValidationError
from app.schemas.user import UserValidationError
from app.services.auth_service import AuthService
from app.services.conversation_service import ConversationService
from app.services.password_service import PasswordService
from app.services.user_service import UserService

logger = logging.getLogger(__name__)

SchemaType = TypeVar("SchemaType", bound=BaseModel)
RouteCallable = TypeVar("RouteCallable", bound=Callable[..., Any])


# === Service Factories ===


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


# === Service Injection Decorators ===


def with_auth_service(func: RouteCallable) -> RouteCallable:
    """Inject AuthService and translate domain errors into HTTP responses."""

    @wraps(func)
    def wrapper(*args: Any, **kwargs: Any):
        auth_service = get_auth_service()
        try:
            return func(*args, auth_service=auth_service, **kwargs)
        except InvalidCredentialsError as exc:
            raise Unauthorized(description=str(exc)) from exc
        except InvalidRefreshTokenError as exc:
            raise Unauthorized(description=str(exc)) from exc
        except AuthServiceError as exc:
            logger.error("Auth service error", exc_info=True)
            raise InternalServerError(description=str(exc)) from exc
        except Exception:  # pragma: no cover - unexpected error path
            logger.error("Unexpected error in auth route", exc_info=True)
            raise

    return wrapper  # type: ignore[return-value]


def with_conversation_service(func: RouteCallable) -> RouteCallable:
    """Inject ConversationService and translate domain errors into HTTP responses."""

    @wraps(func)
    def wrapper(*args: Any, **kwargs: Any):
        service = get_conversation_service()
        try:
            return func(*args, conversation_service=service, **kwargs)
        except ConversationNotFoundError as exc:
            raise NotFound(description=str(exc)) from exc
        except ConversationAccessDeniedError as exc:
            raise Forbidden(description=str(exc)) from exc
        except ConversationServiceError as exc:
            logger.error("Conversation service error", exc_info=True)
            raise InternalServerError(description=str(exc)) from exc
        except Exception:  # pragma: no cover - unexpected error path
            logger.error("Unexpected error in conversation route", exc_info=True)
            raise

    return wrapper  # type: ignore[return-value]


def with_password_service(func: RouteCallable) -> RouteCallable:
    """Inject PasswordService and translate domain errors into HTTP responses."""

    @wraps(func)
    def wrapper(*args: Any, **kwargs: Any):
        password_service = get_password_service()
        try:
            return func(*args, password_service=password_service, **kwargs)
        except InvalidPasswordError as exc:
            raise Unauthorized(description=str(exc)) from exc
        except PasswordChangeFailedError as exc:
            raise InternalServerError(description=str(exc)) from exc
        except PasswordServiceError as exc:
            logger.error("Password service error", exc_info=True)
            raise InternalServerError(description=str(exc)) from exc
        except Exception:  # pragma: no cover - unexpected error path
            logger.error("Unexpected error in password route", exc_info=True)
            raise

    return wrapper  # type: ignore[return-value]


def with_user_service(func: RouteCallable) -> RouteCallable:
    """Inject UserService and translate domain errors into HTTP responses."""

    @wraps(func)
    def wrapper(*args: Any, **kwargs: Any):
        user_service = get_user_service()
        try:
            return func(*args, user_service=user_service, **kwargs)
        except UserAlreadyExistsError as exc:
            raise Conflict(description=str(exc)) from exc
        except UserNotFoundError as exc:
            raise NotFound(description=str(exc)) from exc
        except CannotDeleteAdminError as exc:
            raise Forbidden(description=str(exc)) from exc
        except UserServiceError as exc:
            logger.error("User service error", exc_info=True)
            raise InternalServerError(description=str(exc)) from exc
        except Exception:  # pragma: no cover - unexpected error path
            logger.error("Unexpected error in user route", exc_info=True)
            raise

    return wrapper  # type: ignore[return-value]


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


__all__ = [
    "get_auth_service",
    "get_conversation_service",
    "get_password_service",
    "get_user_service",
    "with_auth_service",
    "with_conversation_service",
    "with_password_service",
    "with_user_service",
    "validate_request_body",
]
