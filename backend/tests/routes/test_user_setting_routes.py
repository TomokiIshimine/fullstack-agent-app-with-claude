"""Tests for user setting routes."""

from __future__ import annotations

from tests.helpers import assert_response_error, assert_response_success, create_auth_client, create_user

# GET /api/users/me/settings tests


class TestGetSettings:
    """Tests for GET /api/users/me/settings endpoint."""

    def test_get_settings_returns_defaults_when_no_record(self, app):
        """Test that GET returns default settings when no record exists."""
        user_id = create_user(app, email="user@example.com")
        user_client = create_auth_client(app, user_id, email="user@example.com", role="user")

        response = user_client.get("/api/users/me/settings")

        data = assert_response_success(response, 200)
        assert data["send_shortcut"] == "enter"

    def test_get_settings_returns_saved_value(self, app):
        """Test that GET returns saved settings after PATCH."""
        user_id = create_user(app, email="user@example.com")
        user_client = create_auth_client(app, user_id, email="user@example.com", role="user")

        # First set the value
        user_client.patch("/api/users/me/settings", json={"send_shortcut": "ctrl_enter"})

        # Then get it
        response = user_client.get("/api/users/me/settings")

        data = assert_response_success(response, 200)
        assert data["send_shortcut"] == "ctrl_enter"

    def test_get_settings_unauthorized_without_auth(self, client):
        """Test that unauthenticated requests are rejected."""
        response = client.get("/api/users/me/settings")

        assert_response_error(response, 401)

    def test_get_settings_response_contains_send_shortcut(self, app):
        """Test that response contains the send_shortcut field."""
        user_id = create_user(app, email="user@example.com")
        user_client = create_auth_client(app, user_id, email="user@example.com", role="user")

        response = user_client.get("/api/users/me/settings")

        data = assert_response_success(response, 200)
        assert "send_shortcut" in data


# PATCH /api/users/me/settings tests


class TestUpdateSettings:
    """Tests for PATCH /api/users/me/settings endpoint."""

    def test_update_settings_to_ctrl_enter(self, app):
        """Test updating send_shortcut to ctrl_enter."""
        user_id = create_user(app, email="user@example.com")
        user_client = create_auth_client(app, user_id, email="user@example.com", role="user")

        response = user_client.patch("/api/users/me/settings", json={"send_shortcut": "ctrl_enter"})

        data = assert_response_success(response, 200)
        assert data["send_shortcut"] == "ctrl_enter"
        assert "message" in data
        assert "更新" in data["message"]

    def test_update_settings_to_enter(self, app):
        """Test updating send_shortcut to enter."""
        user_id = create_user(app, email="user@example.com")
        user_client = create_auth_client(app, user_id, email="user@example.com", role="user")

        response = user_client.patch("/api/users/me/settings", json={"send_shortcut": "enter"})

        data = assert_response_success(response, 200)
        assert data["send_shortcut"] == "enter"

    def test_update_settings_invalid_value(self, app):
        """Test that invalid send_shortcut value is rejected."""
        user_id = create_user(app, email="user@example.com")
        user_client = create_auth_client(app, user_id, email="user@example.com", role="user")

        response = user_client.patch("/api/users/me/settings", json={"send_shortcut": "invalid_value"})

        assert_response_error(response, 400)

    def test_update_settings_missing_body(self, app):
        """Test that request body is required."""
        user_id = create_user(app, email="user@example.com")
        user_client = create_auth_client(app, user_id, email="user@example.com", role="user")

        response = user_client.patch("/api/users/me/settings", data="", content_type="application/json")

        assert_response_error(response, 400)

    def test_update_settings_missing_send_shortcut(self, app):
        """Test that send_shortcut field is required."""
        user_id = create_user(app, email="user@example.com")
        user_client = create_auth_client(app, user_id, email="user@example.com", role="user")

        response = user_client.patch("/api/users/me/settings", json={})

        assert_response_error(response, 400)

    def test_update_settings_unauthorized_without_auth(self, client):
        """Test that unauthenticated requests are rejected."""
        response = client.patch("/api/users/me/settings", json={"send_shortcut": "enter"})

        assert_response_error(response, 401)

    def test_update_settings_upsert_creates_then_updates(self, app):
        """Test that PATCH creates a record on first call and updates on second call."""
        user_id = create_user(app, email="user@example.com")
        user_client = create_auth_client(app, user_id, email="user@example.com", role="user")

        # First PATCH (INSERT)
        response1 = user_client.patch("/api/users/me/settings", json={"send_shortcut": "ctrl_enter"})
        data1 = assert_response_success(response1, 200)
        assert data1["send_shortcut"] == "ctrl_enter"

        # Second PATCH (UPDATE)
        response2 = user_client.patch("/api/users/me/settings", json={"send_shortcut": "enter"})
        data2 = assert_response_success(response2, 200)
        assert data2["send_shortcut"] == "enter"

        # Verify via GET
        response3 = user_client.get("/api/users/me/settings")
        data3 = assert_response_success(response3, 200)
        assert data3["send_shortcut"] == "enter"

    def test_update_settings_does_not_affect_other_users(self, app):
        """Test that updating one user's settings does not affect another user."""
        user1_id = create_user(app, email="user1@example.com")
        user2_id = create_user(app, email="user2@example.com")
        user1_client = create_auth_client(app, user1_id, email="user1@example.com", role="user")
        user2_client = create_auth_client(app, user2_id, email="user2@example.com", role="user")

        # User 1 sets ctrl_enter
        user1_client.patch("/api/users/me/settings", json={"send_shortcut": "ctrl_enter"})

        # User 2 should still have default
        response = user2_client.get("/api/users/me/settings")
        data = assert_response_success(response, 200)
        assert data["send_shortcut"] == "enter"

    def test_update_settings_admin_can_use(self, app):
        """Test that admin users can also use the settings endpoint."""
        admin_id = create_user(app, email="admin@example.com", role="admin")
        admin_client = create_auth_client(app, admin_id, email="admin@example.com", role="admin")

        response = admin_client.patch("/api/users/me/settings", json={"send_shortcut": "ctrl_enter"})

        data = assert_response_success(response, 200)
        assert data["send_shortcut"] == "ctrl_enter"
