from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Literal

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
ENV_PATH = BASE_DIR / ".env"

load_dotenv(dotenv_path=ENV_PATH if ENV_PATH.exists() else None)

DEFAULT_DB_URL = "mysql+pymysql://app_user:example-password@db:3306/app_db"
DEFAULT_LOG_DIR = BASE_DIR / "logs"

# Default JWT secret for development only - MUST be overridden in production
_DEV_JWT_SECRET = "your-secret-key-change-this-in-production"


@dataclass
class DatabaseConfig:
    """Database connection configuration."""

    use_cloud_sql_connector: bool
    database_uri: str
    pool_size: int = 5
    max_overflow: int = 10


@dataclass
class CloudSQLConfig:
    """Cloud SQL Connector specific configuration."""

    instance_connection_name: str
    db_user: str
    db_name: str
    db_pass: str | None
    enable_iam_auth: bool
    ip_type: str = "PRIVATE"  # PRIVATE or PUBLIC (PRIMARY)


def load_database_config() -> DatabaseConfig:
    """Load database configuration from environment variables."""
    use_cloud_sql = os.getenv("USE_CLOUD_SQL_CONNECTOR", "false").lower() == "true"
    database_uri = os.getenv("DATABASE_URL", DEFAULT_DB_URL)
    pool_size = int(os.getenv("DB_POOL_SIZE", "5"))
    max_overflow = int(os.getenv("DB_MAX_OVERFLOW", "10"))

    return DatabaseConfig(
        use_cloud_sql_connector=use_cloud_sql,
        database_uri=database_uri,
        pool_size=pool_size,
        max_overflow=max_overflow,
    )


def load_cloud_sql_config() -> CloudSQLConfig:
    """Load Cloud SQL Connector configuration from environment variables.

    Raises:
        ValueError: If required environment variables are not set.
    """
    instance_connection_name = os.getenv("CLOUDSQL_INSTANCE")
    db_user = os.getenv("DB_USER")
    db_name = os.getenv("DB_NAME")
    enable_iam_auth = os.getenv("ENABLE_IAM_AUTH", "false").lower() == "true"
    ip_type = os.getenv("CLOUDSQL_IP_TYPE", "PRIVATE").upper()

    if not all([instance_connection_name, db_user, db_name]):
        raise ValueError("CLOUDSQL_INSTANCE, DB_USER, and DB_NAME must be set when USE_CLOUD_SQL_CONNECTOR=true")

    # Password is required only when IAM auth is disabled
    db_pass = os.getenv("DB_PASS")
    if not enable_iam_auth and not db_pass:
        raise ValueError("DB_PASS must be set when ENABLE_IAM_AUTH=false")

    # Validate IP type
    if ip_type not in ("PRIVATE", "PUBLIC"):
        raise ValueError(f"CLOUDSQL_IP_TYPE must be 'PRIVATE' or 'PUBLIC', got: {ip_type}")

    return CloudSQLConfig(
        instance_connection_name=instance_connection_name,  # type: ignore
        db_user=db_user,  # type: ignore
        db_name=db_name,  # type: ignore
        db_pass=db_pass,
        enable_iam_auth=enable_iam_auth,
        ip_type=ip_type,
    )


@dataclass
class JWTConfig:
    """JWT token configuration."""

    secret_key: str
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 1440  # 1 day
    refresh_token_expire_days: int = 7


def _get_environment() -> Literal["production", "development", "testing"]:
    """Get the current environment from FLASK_ENV."""
    flask_env = os.getenv("FLASK_ENV", "production").lower()
    if flask_env in ("production", "development", "testing"):
        return flask_env  # type: ignore
    return "production"


def load_jwt_config() -> JWTConfig:
    """Load JWT configuration from environment variables.

    Returns:
        JWTConfig: JWT configuration

    Raises:
        ValueError: If JWT_SECRET_KEY is not set in production environment
    """
    env = _get_environment()
    jwt_secret = os.getenv("JWT_SECRET_KEY")

    # In production, JWT_SECRET_KEY must be explicitly set
    if env == "production" and not jwt_secret:
        raise ValueError(
            "JWT_SECRET_KEY must be set in production environment. "
            "Generate a strong key with: python -c \"import secrets; print(secrets.token_hex(32))\""
        )

    # Use development default only in non-production environments
    if not jwt_secret:
        jwt_secret = _DEV_JWT_SECRET

    return JWTConfig(
        secret_key=jwt_secret,
        algorithm=os.getenv("JWT_ALGORITHM", "HS256"),
        access_token_expire_minutes=int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "1440")),
        refresh_token_expire_days=int(os.getenv("REFRESH_TOKEN_EXPIRE_DAYS", "7")),
    )


@dataclass
class CookieConfig:
    """Cookie configuration for authentication tokens."""

    httponly: bool = True
    samesite: Literal["Strict", "Lax", "None"] = "Lax"
    path: str = "/api"
    secure: bool = False
    domain: str | None = None


def load_cookie_config() -> CookieConfig:
    """Load cookie configuration from environment variables.

    Returns:
        CookieConfig: Cookie configuration
    """
    env = _get_environment()

    # In production, default to secure cookies
    default_secure = "true" if env == "production" else "false"
    cookie_secure = os.getenv("COOKIE_SECURE", default_secure).lower() == "true"

    cookie_domain = os.getenv("COOKIE_DOMAIN")

    return CookieConfig(
        httponly=True,
        samesite="Lax",
        path="/api",
        secure=cookie_secure,
        domain=cookie_domain if cookie_domain else None,
    )


@dataclass
class RateLimitConfig:
    """Rate limiting configuration."""

    enabled: bool = False
    default_limits: list[str] = field(default_factory=lambda: ["200 per hour", "50 per minute"])
    login_limit: str = "10 per minute"
    refresh_limit: str = "30 per minute"
    logout_limit: str = "20 per minute"
    strategy: str = "fixed-window"
    headers_enabled: bool = True
    swallow_errors: bool = True
    # Redis configuration
    redis_host: str | None = None
    redis_port: int = 6379
    redis_password: str | None = None


def load_rate_limit_config() -> RateLimitConfig:
    """Load rate limit configuration from environment variables.

    Returns:
        RateLimitConfig: Rate limit configuration
    """
    enabled = os.getenv("RATE_LIMIT_ENABLED", "false").lower() == "true"

    redis_host = os.getenv("REDIS_HOST")
    redis_port = int(os.getenv("REDIS_PORT", "6379"))
    redis_password = os.getenv("REDIS_PASSWORD")

    return RateLimitConfig(
        enabled=enabled,
        default_limits=["200 per hour", "50 per minute"],
        login_limit=os.getenv("RATE_LIMIT_LOGIN", "10 per minute"),
        refresh_limit=os.getenv("RATE_LIMIT_REFRESH", "30 per minute"),
        logout_limit=os.getenv("RATE_LIMIT_LOGOUT", "20 per minute"),
        strategy=os.getenv("RATE_LIMIT_STRATEGY", "fixed-window"),
        headers_enabled=os.getenv("RATE_LIMIT_HEADERS", "true").lower() == "true",
        swallow_errors=os.getenv("RATE_LIMIT_SWALLOW_ERRORS", "true").lower() == "true",
        redis_host=redis_host,
        redis_port=redis_port,
        redis_password=redis_password,
    )


def get_rate_limit_storage_uri(config: RateLimitConfig | None = None) -> str:
    """Get storage URI for Flask-Limiter.

    Args:
        config: Optional rate limit config. If not provided, loads from environment.

    Returns:
        Redis URI if configured and enabled, otherwise "memory://"
    """
    if config is None:
        config = load_rate_limit_config()

    if not config.enabled:
        return "memory://"

    if not config.redis_host:
        return "memory://"

    # Construct Redis URI
    if config.redis_password:
        return f"redis://:{config.redis_password}@{config.redis_host}:{config.redis_port}/0"
    return f"redis://{config.redis_host}:{config.redis_port}/0"


class Config:
    """Base configuration loaded from environment variables."""

    SQLALCHEMY_DATABASE_URI = os.getenv("DATABASE_URL", DEFAULT_DB_URL)
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Logging configuration
    LOG_DIR = os.getenv("LOG_DIR", str(DEFAULT_LOG_DIR))
    FLASK_ENV = os.getenv("FLASK_ENV", "production")

    # Set TESTING flag for test environment
    TESTING = FLASK_ENV == "testing"

    # Determine log level based on environment
    # Development/Testing: DEBUG, Production: INFO
    _env_log_level = os.getenv("LOG_LEVEL")
    if _env_log_level:
        LOG_LEVEL = _env_log_level.upper()
    else:
        LOG_LEVEL = "DEBUG" if FLASK_ENV in ("development", "testing") else "INFO"

    @classmethod
    def refresh(cls) -> None:
        """Reload env vars into config. Useful for tests."""
        cls.SQLALCHEMY_DATABASE_URI = os.getenv("DATABASE_URL", DEFAULT_DB_URL)
        cls.LOG_DIR = os.getenv("LOG_DIR", str(DEFAULT_LOG_DIR))
        cls.FLASK_ENV = os.getenv("FLASK_ENV", "production")
        cls.TESTING = cls.FLASK_ENV == "testing"
        _env_log_level = os.getenv("LOG_LEVEL")
        if _env_log_level:
            cls.LOG_LEVEL = _env_log_level.upper()
        else:
            cls.LOG_LEVEL = "DEBUG" if cls.FLASK_ENV in ("development", "testing") else "INFO"
