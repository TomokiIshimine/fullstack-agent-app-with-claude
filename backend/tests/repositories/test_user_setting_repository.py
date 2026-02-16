"""Tests for UserSettingRepository (user setting data access layer)."""

from __future__ import annotations

import pytest

from app.models.user_setting import UserSetting
from app.repositories.user_setting_repository import UserSettingRepository
from tests.helpers import create_user


@pytest.fixture
def setting_repo(app):
    """Create UserSettingRepository instance with test database session."""
    from app.database import get_session

    with app.app_context():
        session = get_session()
        yield UserSettingRepository(session), session


class TestUserSettingRepositoryFindByUserId:
    """Tests for UserSettingRepository.find_by_user_id method."""

    def test_find_by_user_id_returns_none_when_no_setting(self, app, setting_repo):
        """Test that find_by_user_id returns None when no setting exists."""
        repo, session = setting_repo
        user_id = create_user(app, email="user@example.com")
        with app.app_context():
            result = repo.find_by_user_id(user_id)
            assert result is None

    def test_find_by_user_id_returns_setting_when_exists(self, app, setting_repo):
        """Test that find_by_user_id returns UserSetting when it exists."""
        repo, session = setting_repo
        user_id = create_user(app, email="user@example.com")
        with app.app_context():
            repo.create(user_id=user_id, send_shortcut="enter")
            result = repo.find_by_user_id(user_id)

            assert result is not None
            assert isinstance(result, UserSetting)
            assert result.user_id == user_id
            assert result.send_shortcut == "enter"

    def test_find_by_user_id_returns_correct_user_setting(self, app, setting_repo):
        """Test that find_by_user_id returns the correct user's setting."""
        repo, session = setting_repo
        user1_id = create_user(app, email="user1@example.com")
        user2_id = create_user(app, email="user2@example.com")
        with app.app_context():
            repo.create(user_id=user1_id, send_shortcut="enter")
            repo.create(user_id=user2_id, send_shortcut="ctrl_enter")

            result1 = repo.find_by_user_id(user1_id)
            result2 = repo.find_by_user_id(user2_id)

            assert result1.send_shortcut == "enter"
            assert result2.send_shortcut == "ctrl_enter"


class TestUserSettingRepositoryCreate:
    """Tests for UserSettingRepository.create method."""

    def test_create_returns_user_setting_instance(self, app, setting_repo):
        """Test that create returns a UserSetting instance."""
        repo, session = setting_repo
        user_id = create_user(app, email="user@example.com")
        with app.app_context():
            result = repo.create(user_id=user_id, send_shortcut="enter")

            assert isinstance(result, UserSetting)
            assert result.id is not None

    def test_create_sets_user_id(self, app, setting_repo):
        """Test that create sets the user_id correctly."""
        repo, session = setting_repo
        user_id = create_user(app, email="user@example.com")
        with app.app_context():
            result = repo.create(user_id=user_id, send_shortcut="enter")

            assert result.user_id == user_id

    def test_create_sets_send_shortcut(self, app, setting_repo):
        """Test that create sets the send_shortcut correctly."""
        repo, session = setting_repo
        user_id = create_user(app, email="user@example.com")
        with app.app_context():
            result = repo.create(user_id=user_id, send_shortcut="ctrl_enter")

            assert result.send_shortcut == "ctrl_enter"

    def test_create_with_default_send_shortcut(self, app, setting_repo):
        """Test that create uses default 'enter' for send_shortcut."""
        repo, session = setting_repo
        user_id = create_user(app, email="user@example.com")
        with app.app_context():
            result = repo.create(user_id=user_id)

            assert result.send_shortcut == "enter"

    def test_create_sets_timestamps(self, app, setting_repo):
        """Test that create sets created_at and updated_at timestamps."""
        repo, session = setting_repo
        user_id = create_user(app, email="user@example.com")
        with app.app_context():
            result = repo.create(user_id=user_id, send_shortcut="enter")

            assert result.created_at is not None
            assert result.updated_at is not None


class TestUserSettingRepositoryUpdate:
    """Tests for UserSettingRepository.update method."""

    def test_update_changes_send_shortcut(self, app, setting_repo):
        """Test that update changes the send_shortcut value."""
        repo, session = setting_repo
        user_id = create_user(app, email="user@example.com")
        with app.app_context():
            setting = repo.create(user_id=user_id, send_shortcut="enter")

            result = repo.update(setting, send_shortcut="ctrl_enter")

            assert result.send_shortcut == "ctrl_enter"

    def test_update_returns_updated_instance(self, app, setting_repo):
        """Test that update returns the updated UserSetting instance."""
        repo, session = setting_repo
        user_id = create_user(app, email="user@example.com")
        with app.app_context():
            setting = repo.create(user_id=user_id, send_shortcut="enter")

            result = repo.update(setting, send_shortcut="ctrl_enter")

            assert isinstance(result, UserSetting)
            assert result.id == setting.id

    def test_update_persists_in_database(self, app, setting_repo):
        """Test that update persists the change in the database."""
        repo, session = setting_repo
        user_id = create_user(app, email="user@example.com")
        with app.app_context():
            setting = repo.create(user_id=user_id, send_shortcut="enter")
            repo.update(setting, send_shortcut="ctrl_enter")

            # Re-fetch from database
            refreshed = repo.find_by_user_id(user_id)
            assert refreshed.send_shortcut == "ctrl_enter"

    def test_update_preserves_user_id(self, app, setting_repo):
        """Test that update does not change user_id."""
        repo, session = setting_repo
        user_id = create_user(app, email="user@example.com")
        with app.app_context():
            setting = repo.create(user_id=user_id, send_shortcut="enter")

            result = repo.update(setting, send_shortcut="ctrl_enter")

            assert result.user_id == user_id


class TestUserSettingRepositoryIntegration:
    """Integration tests for UserSettingRepository."""

    def test_full_setting_lifecycle(self, app, setting_repo):
        """Test complete setting lifecycle: create, read, update, read."""
        repo, session = setting_repo
        user_id = create_user(app, email="user@example.com")
        with app.app_context():
            # Create
            setting = repo.create(user_id=user_id, send_shortcut="enter")
            assert setting.id is not None

            # Read
            found = repo.find_by_user_id(user_id)
            assert found is not None
            assert found.send_shortcut == "enter"

            # Update
            repo.update(found, send_shortcut="ctrl_enter")

            # Read again
            updated = repo.find_by_user_id(user_id)
            assert updated.send_shortcut == "ctrl_enter"
