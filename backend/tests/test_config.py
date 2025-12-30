"""Tests for configuration loading functions."""

from __future__ import annotations

import os
from unittest.mock import patch

import pytest

from app.config import (
    CookieConfig,
    JWTConfig,
    RateLimitConfig,
    _get_environment,
    get_rate_limit_storage_uri,
    load_cookie_config,
    load_jwt_config,
    load_rate_limit_config,
)


class TestGetEnvironment:
    """Tests for _get_environment function."""

    def test_default_to_production(self):
        """Test that environment defaults to production when FLASK_ENV is not set."""
        with patch.dict(os.environ, {}, clear=True):
            # Remove FLASK_ENV if it exists
            os.environ.pop("FLASK_ENV", None)
            assert _get_environment() == "production"

    def test_development_environment(self):
        """Test that development environment is correctly detected."""
        with patch.dict(os.environ, {"FLASK_ENV": "development"}):
            assert _get_environment() == "development"

    def test_testing_environment(self):
        """Test that testing environment is correctly detected."""
        with patch.dict(os.environ, {"FLASK_ENV": "testing"}):
            assert _get_environment() == "testing"

    def test_production_environment(self):
        """Test that production environment is correctly detected."""
        with patch.dict(os.environ, {"FLASK_ENV": "production"}):
            assert _get_environment() == "production"

    def test_unknown_environment_defaults_to_production(self):
        """Test that unknown environment defaults to production."""
        with patch.dict(os.environ, {"FLASK_ENV": "unknown"}):
            assert _get_environment() == "production"


class TestLoadJWTConfig:
    """Tests for load_jwt_config function."""

    def test_load_jwt_config_development_with_defaults(self):
        """Test loading JWT config in development with default values."""
        with patch.dict(
            os.environ,
            {
                "FLASK_ENV": "development",
            },
            clear=True,
        ):
            # Remove JWT_SECRET_KEY if it exists
            os.environ.pop("JWT_SECRET_KEY", None)
            config = load_jwt_config()
            assert config.secret_key == "your-secret-key-change-this-in-production"
            assert config.algorithm == "HS256"
            assert config.access_token_expire_minutes == 1440
            assert config.refresh_token_expire_days == 7

    def test_load_jwt_config_with_custom_values(self):
        """Test loading JWT config with custom environment variables."""
        with patch.dict(
            os.environ,
            {
                "FLASK_ENV": "development",
                "JWT_SECRET_KEY": "my-custom-secret-key",
                "JWT_ALGORITHM": "HS512",
                "ACCESS_TOKEN_EXPIRE_MINUTES": "60",
                "REFRESH_TOKEN_EXPIRE_DAYS": "30",
            },
        ):
            config = load_jwt_config()
            assert config.secret_key == "my-custom-secret-key"
            assert config.algorithm == "HS512"
            assert config.access_token_expire_minutes == 60
            assert config.refresh_token_expire_days == 30

    def test_load_jwt_config_production_requires_secret_key(self):
        """Test that production environment requires JWT_SECRET_KEY."""
        with patch.dict(os.environ, {"FLASK_ENV": "production"}, clear=True):
            os.environ.pop("JWT_SECRET_KEY", None)
            with pytest.raises(ValueError) as excinfo:
                load_jwt_config()
            assert "JWT_SECRET_KEY must be set in production environment" in str(excinfo.value)

    def test_load_jwt_config_production_with_secret_key(self):
        """Test loading JWT config in production with secret key set."""
        with patch.dict(
            os.environ,
            {
                "FLASK_ENV": "production",
                "JWT_SECRET_KEY": "production-secret-key",
            },
        ):
            config = load_jwt_config()
            assert config.secret_key == "production-secret-key"

    def test_load_jwt_config_testing_with_defaults(self):
        """Test loading JWT config in testing with default values."""
        with patch.dict(
            os.environ,
            {
                "FLASK_ENV": "testing",
            },
            clear=True,
        ):
            os.environ.pop("JWT_SECRET_KEY", None)
            config = load_jwt_config()
            assert config.secret_key == "your-secret-key-change-this-in-production"


class TestLoadCookieConfig:
    """Tests for load_cookie_config function."""

    def test_load_cookie_config_development_defaults(self):
        """Test loading cookie config in development with default values."""
        with patch.dict(
            os.environ,
            {
                "FLASK_ENV": "development",
            },
            clear=True,
        ):
            os.environ.pop("COOKIE_SECURE", None)
            os.environ.pop("COOKIE_DOMAIN", None)
            config = load_cookie_config()
            assert config.httponly is True
            assert config.samesite == "Lax"
            assert config.path == "/api"
            assert config.secure is False
            assert config.domain is None

    def test_load_cookie_config_production_defaults_to_secure(self):
        """Test that production environment defaults to secure cookies."""
        with patch.dict(
            os.environ,
            {
                "FLASK_ENV": "production",
            },
            clear=True,
        ):
            os.environ.pop("COOKIE_SECURE", None)
            os.environ.pop("COOKIE_DOMAIN", None)
            config = load_cookie_config()
            assert config.secure is True

    def test_load_cookie_config_with_custom_values(self):
        """Test loading cookie config with custom environment variables."""
        with patch.dict(
            os.environ,
            {
                "FLASK_ENV": "development",
                "COOKIE_SECURE": "true",
                "COOKIE_DOMAIN": "example.com",
            },
        ):
            config = load_cookie_config()
            assert config.secure is True
            assert config.domain == "example.com"

    def test_load_cookie_config_empty_domain_is_none(self):
        """Test that empty COOKIE_DOMAIN is treated as None."""
        with patch.dict(
            os.environ,
            {
                "FLASK_ENV": "development",
                "COOKIE_DOMAIN": "",
            },
        ):
            config = load_cookie_config()
            assert config.domain is None


class TestLoadRateLimitConfig:
    """Tests for load_rate_limit_config function."""

    def test_load_rate_limit_config_defaults(self):
        """Test loading rate limit config with default values."""
        with patch.dict(os.environ, {}, clear=True):
            os.environ.pop("RATE_LIMIT_ENABLED", None)
            os.environ.pop("REDIS_HOST", None)
            config = load_rate_limit_config()
            assert config.enabled is False
            assert config.default_limits == ["200 per hour", "50 per minute"]
            assert config.login_limit == "10 per minute"
            assert config.refresh_limit == "30 per minute"
            assert config.logout_limit == "20 per minute"
            assert config.strategy == "fixed-window"
            assert config.headers_enabled is True
            assert config.swallow_errors is True
            assert config.redis_host is None

    def test_load_rate_limit_config_enabled(self):
        """Test loading rate limit config when enabled."""
        with patch.dict(
            os.environ,
            {
                "RATE_LIMIT_ENABLED": "true",
                "REDIS_HOST": "localhost",
                "REDIS_PORT": "6380",
                "REDIS_PASSWORD": "mypassword",
            },
        ):
            config = load_rate_limit_config()
            assert config.enabled is True
            assert config.redis_host == "localhost"
            assert config.redis_port == 6380
            assert config.redis_password == "mypassword"

    def test_load_rate_limit_config_custom_limits(self):
        """Test loading rate limit config with custom rate limits."""
        with patch.dict(
            os.environ,
            {
                "RATE_LIMIT_LOGIN": "5 per minute",
                "RATE_LIMIT_REFRESH": "20 per minute",
                "RATE_LIMIT_LOGOUT": "10 per minute",
            },
        ):
            config = load_rate_limit_config()
            assert config.login_limit == "5 per minute"
            assert config.refresh_limit == "20 per minute"
            assert config.logout_limit == "10 per minute"


class TestGetRateLimitStorageUri:
    """Tests for get_rate_limit_storage_uri function."""

    def test_returns_memory_when_disabled(self):
        """Test that memory URI is returned when rate limiting is disabled."""
        config = RateLimitConfig(enabled=False)
        assert get_rate_limit_storage_uri(config) == "memory://"

    def test_returns_memory_when_no_redis_host(self):
        """Test that memory URI is returned when Redis host is not configured."""
        config = RateLimitConfig(enabled=True, redis_host=None)
        assert get_rate_limit_storage_uri(config) == "memory://"

    def test_returns_redis_uri_without_password(self):
        """Test Redis URI without password."""
        config = RateLimitConfig(
            enabled=True,
            redis_host="localhost",
            redis_port=6379,
            redis_password=None,
        )
        assert get_rate_limit_storage_uri(config) == "redis://localhost:6379/0"

    def test_returns_redis_uri_with_password(self):
        """Test Redis URI with password."""
        config = RateLimitConfig(
            enabled=True,
            redis_host="localhost",
            redis_port=6379,
            redis_password="mypassword",
        )
        assert get_rate_limit_storage_uri(config) == "redis://:mypassword@localhost:6379/0"

    def test_returns_redis_uri_with_custom_port(self):
        """Test Redis URI with custom port."""
        config = RateLimitConfig(
            enabled=True,
            redis_host="redis.example.com",
            redis_port=6380,
            redis_password=None,
        )
        assert get_rate_limit_storage_uri(config) == "redis://redis.example.com:6380/0"


class TestJWTConfigDataclass:
    """Tests for JWTConfig dataclass."""

    def test_jwt_config_defaults(self):
        """Test JWTConfig default values."""
        config = JWTConfig(secret_key="test-secret")
        assert config.secret_key == "test-secret"
        assert config.algorithm == "HS256"
        assert config.access_token_expire_minutes == 1440
        assert config.refresh_token_expire_days == 7

    def test_jwt_config_custom_values(self):
        """Test JWTConfig with custom values."""
        config = JWTConfig(
            secret_key="custom-secret",
            algorithm="HS512",
            access_token_expire_minutes=60,
            refresh_token_expire_days=14,
        )
        assert config.secret_key == "custom-secret"
        assert config.algorithm == "HS512"
        assert config.access_token_expire_minutes == 60
        assert config.refresh_token_expire_days == 14


class TestCookieConfigDataclass:
    """Tests for CookieConfig dataclass."""

    def test_cookie_config_defaults(self):
        """Test CookieConfig default values."""
        config = CookieConfig()
        assert config.httponly is True
        assert config.samesite == "Lax"
        assert config.path == "/api"
        assert config.secure is False
        assert config.domain is None

    def test_cookie_config_custom_values(self):
        """Test CookieConfig with custom values."""
        config = CookieConfig(
            httponly=True,
            samesite="Strict",
            path="/auth",
            secure=True,
            domain="example.com",
        )
        assert config.httponly is True
        assert config.samesite == "Strict"
        assert config.path == "/auth"
        assert config.secure is True
        assert config.domain == "example.com"


class TestRateLimitConfigDataclass:
    """Tests for RateLimitConfig dataclass."""

    def test_rate_limit_config_defaults(self):
        """Test RateLimitConfig default values."""
        config = RateLimitConfig()
        assert config.enabled is False
        assert config.default_limits == ["200 per hour", "50 per minute"]
        assert config.login_limit == "10 per minute"
        assert config.refresh_limit == "30 per minute"
        assert config.logout_limit == "20 per minute"
        assert config.strategy == "fixed-window"
        assert config.headers_enabled is True
        assert config.swallow_errors is True
        assert config.redis_host is None
        assert config.redis_port == 6379
        assert config.redis_password is None
