"""Tests for UserSettingService (user setting business logic)."""

from __future__ import annotations

import pytest

from app.services.user_setting_service import DEFAULT_SEND_SHORTCUT, UserSettingService
from tests.helpers import create_user


@pytest.fixture
def user_setting_service(app):
    """Create UserSettingService instance with test database session."""
    from app.database import get_session

    with app.app_context():
        session = get_session()
        yield UserSettingService(session)


# get_settings tests


class TestGetSettings:
    """Tests for UserSettingService.get_settings method."""

    def test_get_settings_returns_defaults_when_no_record(self, app, user_setting_service):
        """Test that get_settings returns defaults when no record exists."""
        user_id = create_user(app, email="user@example.com")

        result = user_setting_service.get_settings(user_id)

        assert result == {"send_shortcut": DEFAULT_SEND_SHORTCUT}
        assert result["send_shortcut"] == "enter"

    def test_get_settings_returns_saved_value(self, app, user_setting_service):
        """Test that get_settings returns saved value when record exists."""
        user_id = create_user(app, email="user@example.com")

        # Create a setting first
        user_setting_service.update_settings(user_id, send_shortcut="ctrl_enter")

        result = user_setting_service.get_settings(user_id)

        assert result == {"send_shortcut": "ctrl_enter"}

    def test_get_settings_returns_enter_value(self, app, user_setting_service):
        """Test that get_settings returns 'enter' when explicitly set."""
        user_id = create_user(app, email="user@example.com")

        # Create a setting with enter
        user_setting_service.update_settings(user_id, send_shortcut="enter")

        result = user_setting_service.get_settings(user_id)

        assert result == {"send_shortcut": "enter"}

    def test_get_settings_different_users_independent(self, app, user_setting_service):
        """Test that settings for different users are independent."""
        user1_id = create_user(app, email="user1@example.com")
        user2_id = create_user(app, email="user2@example.com")

        user_setting_service.update_settings(user1_id, send_shortcut="ctrl_enter")
        # user2 has no settings

        result1 = user_setting_service.get_settings(user1_id)
        result2 = user_setting_service.get_settings(user2_id)

        assert result1["send_shortcut"] == "ctrl_enter"
        assert result2["send_shortcut"] == "enter"  # default


# update_settings tests


class TestUpdateSettings:
    """Tests for UserSettingService.update_settings method."""

    def test_update_settings_creates_when_no_record(self, app, user_setting_service):
        """Test that update_settings creates a record when none exists (upsert INSERT)."""
        user_id = create_user(app, email="user@example.com")

        result = user_setting_service.update_settings(user_id, send_shortcut="ctrl_enter")

        assert result == {"send_shortcut": "ctrl_enter"}

        # Verify it was persisted
        settings = user_setting_service.get_settings(user_id)
        assert settings["send_shortcut"] == "ctrl_enter"

    def test_update_settings_updates_existing_record(self, app, user_setting_service):
        """Test that update_settings updates an existing record (upsert UPDATE)."""
        user_id = create_user(app, email="user@example.com")

        # First create
        user_setting_service.update_settings(user_id, send_shortcut="enter")

        # Then update
        result = user_setting_service.update_settings(user_id, send_shortcut="ctrl_enter")

        assert result == {"send_shortcut": "ctrl_enter"}

        # Verify it was persisted
        settings = user_setting_service.get_settings(user_id)
        assert settings["send_shortcut"] == "ctrl_enter"

    def test_update_settings_returns_new_value(self, app, user_setting_service):
        """Test that update_settings returns the new setting value."""
        user_id = create_user(app, email="user@example.com")

        result = user_setting_service.update_settings(user_id, send_shortcut="enter")

        assert result["send_shortcut"] == "enter"

    def test_update_settings_multiple_times(self, app, user_setting_service):
        """Test that settings can be updated multiple times."""
        user_id = create_user(app, email="user@example.com")

        user_setting_service.update_settings(user_id, send_shortcut="enter")
        user_setting_service.update_settings(user_id, send_shortcut="ctrl_enter")
        user_setting_service.update_settings(user_id, send_shortcut="enter")

        result = user_setting_service.get_settings(user_id)
        assert result["send_shortcut"] == "enter"

    def test_update_settings_does_not_affect_other_users(self, app, user_setting_service):
        """Test that updating one user's settings does not affect others."""
        user1_id = create_user(app, email="user1@example.com")
        user2_id = create_user(app, email="user2@example.com")

        user_setting_service.update_settings(user1_id, send_shortcut="enter")
        user_setting_service.update_settings(user2_id, send_shortcut="ctrl_enter")

        # Update user1 only
        user_setting_service.update_settings(user1_id, send_shortcut="ctrl_enter")

        # user2 should be unchanged
        result2 = user_setting_service.get_settings(user2_id)
        assert result2["send_shortcut"] == "ctrl_enter"
