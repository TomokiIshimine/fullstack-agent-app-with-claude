"""Tests for common schema validators."""

from __future__ import annotations

import pytest

from app.schemas.validators import (
    MAX_MESSAGE_LENGTH,
    MIN_PASSWORD_LENGTH,
    PasswordValidationError,
    validate_message_content,
    validate_password,
)


class TestPasswordValidator:
    """Tests for validate_password function."""

    def test_valid_password(self):
        """Test that a valid password passes validation."""
        result = validate_password("password123")
        assert result == "password123"

    def test_valid_password_with_special_chars(self):
        """Test that a password with special characters passes validation."""
        result = validate_password("P@ssw0rd!")
        assert result == "P@ssw0rd!"

    def test_password_too_short(self):
        """Test that a password shorter than MIN_PASSWORD_LENGTH fails."""
        with pytest.raises(ValueError) as exc_info:
            validate_password("short1")
        assert f"at least {MIN_PASSWORD_LENGTH} characters" in str(exc_info.value)

    def test_password_empty(self):
        """Test that an empty password fails."""
        with pytest.raises(ValueError) as exc_info:
            validate_password("")
        assert f"at least {MIN_PASSWORD_LENGTH} characters" in str(exc_info.value)

    def test_password_no_letters(self):
        """Test that a password without letters fails."""
        with pytest.raises(ValueError) as exc_info:
            validate_password("12345678")
        assert "contain both letters and numbers" in str(exc_info.value)

    def test_password_no_numbers(self):
        """Test that a password without numbers fails."""
        with pytest.raises(ValueError) as exc_info:
            validate_password("onlyletters")
        assert "contain both letters and numbers" in str(exc_info.value)

    def test_password_with_custom_exception(self):
        """Test that custom exception class is used when specified."""
        with pytest.raises(PasswordValidationError) as exc_info:
            validate_password("short1", exception_class=PasswordValidationError)
        assert f"at least {MIN_PASSWORD_LENGTH} characters" in str(exc_info.value)

    def test_password_exactly_min_length(self):
        """Test that a password exactly at MIN_PASSWORD_LENGTH passes."""
        # 8 characters with letters and numbers
        result = validate_password("abcdef12")
        assert result == "abcdef12"

    def test_password_min_length_constant(self):
        """Test that MIN_PASSWORD_LENGTH is 8."""
        assert MIN_PASSWORD_LENGTH == 8


class TestMessageContentValidator:
    """Tests for validate_message_content function."""

    def test_valid_content(self):
        """Test that valid content passes validation."""
        result = validate_message_content("Hello, world!")
        assert result == "Hello, world!"

    def test_content_trimmed(self):
        """Test that content is trimmed."""
        result = validate_message_content("  Hello, world!  ")
        assert result == "Hello, world!"

    def test_content_empty(self):
        """Test that empty content fails."""
        with pytest.raises(ValueError) as exc_info:
            validate_message_content("")
        assert "Content is required" in str(exc_info.value)

    def test_content_whitespace_only(self):
        """Test that whitespace-only content fails."""
        with pytest.raises(ValueError) as exc_info:
            validate_message_content("   ")
        assert "Content is required" in str(exc_info.value)

    def test_content_too_long(self):
        """Test that content exceeding MAX_MESSAGE_LENGTH fails."""
        long_content = "a" * (MAX_MESSAGE_LENGTH + 1)
        with pytest.raises(ValueError) as exc_info:
            validate_message_content(long_content)
        assert f"at most {MAX_MESSAGE_LENGTH} characters" in str(exc_info.value)

    def test_content_exactly_max_length(self):
        """Test that content exactly at MAX_MESSAGE_LENGTH passes."""
        content = "a" * MAX_MESSAGE_LENGTH
        result = validate_message_content(content)
        assert result == content

    def test_custom_field_name_in_error(self):
        """Test that custom field name is used in error messages."""
        with pytest.raises(ValueError) as exc_info:
            validate_message_content("", field_name="Message")
        assert "Message is required" in str(exc_info.value)

    def test_custom_field_name_max_length_error(self):
        """Test that custom field name is used in max length error."""
        long_content = "a" * (MAX_MESSAGE_LENGTH + 1)
        with pytest.raises(ValueError) as exc_info:
            validate_message_content(long_content, field_name="Message")
        assert f"Message must be at most {MAX_MESSAGE_LENGTH} characters" in str(
            exc_info.value
        )

    def test_max_message_length_constant(self):
        """Test that MAX_MESSAGE_LENGTH is 32000."""
        assert MAX_MESSAGE_LENGTH == 32000


class TestPasswordValidationError:
    """Tests for PasswordValidationError class."""

    def test_is_value_error_subclass(self):
        """Test that PasswordValidationError is a subclass of ValueError."""
        assert issubclass(PasswordValidationError, ValueError)

    def test_can_be_raised(self):
        """Test that PasswordValidationError can be raised and caught."""
        with pytest.raises(PasswordValidationError):
            raise PasswordValidationError("Test error")

    def test_can_be_caught_as_value_error(self):
        """Test that PasswordValidationError can be caught as ValueError."""
        with pytest.raises(ValueError):
            raise PasswordValidationError("Test error")
