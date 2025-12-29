"""Tests for conversation routes."""


class TestConversationRoutes:
    """Test conversation API routes."""

    def test_list_conversations_unauthenticated(self, client):
        """Unauthenticated users should receive 401."""
        response = client.get("/api/conversations")
        assert response.status_code == 401

    def test_list_conversations_empty(self, auth_client):
        """Authenticated user with no conversations should get empty list."""
        response = auth_client.get("/api/conversations")
        assert response.status_code == 200
        data = response.get_json()
        assert "conversations" in data
        assert data["conversations"] == []
        assert "meta" in data

    def test_create_conversation_unauthenticated(self, client):
        """Unauthenticated users should receive 401."""
        response = client.post(
            "/api/conversations",
            json={"content": "Hello"},
            content_type="application/json",
        )
        assert response.status_code == 401

    def test_create_conversation_missing_content(self, auth_client):
        """Missing content should return 400."""
        response = auth_client.post(
            "/api/conversations",
            json={},
            content_type="application/json",
        )
        assert response.status_code == 400

    def test_create_conversation_non_streaming(self, auth_client, mocker):
        """Test creating a conversation in non-streaming mode."""
        # Mock Agent service to avoid external API calls
        mock_agent_service = mocker.patch("app.services.conversation_service.AgentService")
        mock_agent_service.return_value.generate_title.return_value = "Test Title"

        response = auth_client.post(
            "/api/conversations",
            json={"message": "Hello, this is a test"},
            content_type="application/json",
            headers={"X-Stream": "false"},
        )
        assert response.status_code == 201
        data = response.get_json()
        assert "conversation" in data
        assert "message" in data
        assert data["conversation"]["title"] == "Test Title"
        assert data["message"]["content"] == "Hello, this is a test"
        assert data["message"]["role"] == "user"

    # Note: Streaming tests are skipped in unit tests due to SQLite locking issues
    # with Flask test client and SSE generators. Streaming functionality is tested
    # via E2E tests with a real database connection.

    def test_get_conversation_unauthenticated(self, client):
        """Unauthenticated users should receive 401."""
        response = client.get("/api/conversations/some-uuid")
        assert response.status_code == 401

    def test_get_conversation_not_found(self, auth_client):
        """Non-existent conversation should return 404."""
        response = auth_client.get("/api/conversations/nonexistent-uuid")
        assert response.status_code == 404

    def test_delete_conversation_unauthenticated(self, client):
        """Unauthenticated users should receive 401."""
        response = client.delete("/api/conversations/some-uuid")
        assert response.status_code == 401

    def test_delete_conversation_not_found(self, auth_client):
        """Non-existent conversation should return 404."""
        response = auth_client.delete("/api/conversations/nonexistent-uuid")
        assert response.status_code == 404


class TestConversationMessagesRoute:
    """Test conversation messages API route."""

    def test_send_message_unauthenticated(self, client):
        """Unauthenticated users should receive 401."""
        response = client.post(
            "/api/conversations/some-uuid/messages",
            json={"content": "Hello"},
            content_type="application/json",
        )
        assert response.status_code == 401

    def test_send_message_missing_content(self, auth_client):
        """Missing content should return 400."""
        response = auth_client.post(
            "/api/conversations/some-uuid/messages",
            json={},
            content_type="application/json",
        )
        assert response.status_code == 400

    def test_send_message_conversation_not_found(self, auth_client):
        """Non-existent conversation should return 404 (non-streaming mode)."""
        response = auth_client.post(
            "/api/conversations/nonexistent-uuid/messages",
            json={"content": "Hello"},
            content_type="application/json",
            headers={"X-Stream": "false"},
        )
        assert response.status_code == 404


class TestConversationModels:
    """Test conversation and message models."""

    def test_conversation_model_creation(self, app, test_user):
        """Test creating a conversation model."""
        from app.database import get_session
        from app.models import Conversation

        with app.app_context():
            session = get_session()

            # Create a conversation
            conversation = Conversation(
                user_id=test_user,
                title="Test Conversation",
            )
            session.add(conversation)
            session.commit()

            # Verify the conversation was created
            assert conversation.id is not None
            assert conversation.uuid is not None
            assert conversation.title == "Test Conversation"
            assert conversation.user_id == test_user

    def test_message_model_creation(self, app, test_user):
        """Test creating a message model."""
        from app.database import get_session
        from app.models import Conversation, Message

        with app.app_context():
            session = get_session()

            # Create a conversation
            conversation = Conversation(
                user_id=test_user,
                title="Test Conversation",
            )
            session.add(conversation)
            session.commit()

            # Create a message
            message = Message(
                conversation_id=conversation.id,
                role="user",
                content="Hello, this is a test message",
            )
            session.add(message)
            session.commit()

            # Verify the message was created
            assert message.id is not None
            assert message.role == "user"
            assert message.content == "Hello, this is a test message"
            assert message.conversation_id == conversation.id

    def test_conversation_messages_relationship(self, app, test_user):
        """Test the relationship between conversation and messages."""
        from app.database import get_session
        from app.models import Conversation, Message

        with app.app_context():
            session = get_session()

            # Create a conversation
            conversation = Conversation(
                user_id=test_user,
                title="Test Conversation",
            )
            session.add(conversation)
            session.commit()

            # Create messages
            user_message = Message(
                conversation_id=conversation.id,
                role="user",
                content="Hello",
            )
            assistant_message = Message(
                conversation_id=conversation.id,
                role="assistant",
                content="Hi there!",
            )
            session.add_all([user_message, assistant_message])
            session.commit()

            # Refresh conversation to get the relationship
            session.refresh(conversation)

            # Verify relationship
            assert len(conversation.messages) == 2
            assert conversation.messages[0].role == "user"
            assert conversation.messages[1].role == "assistant"


class TestConversationRepository:
    """Test conversation repository."""

    def test_create_conversation(self, app, test_user):
        """Test creating a conversation through repository."""
        from app.database import get_session
        from app.repositories.conversation_repository import ConversationRepository

        with app.app_context():
            session = get_session()
            repo = ConversationRepository(session)

            conversation = repo.create(user_id=test_user, title="Repo Test")

            assert conversation.id is not None
            assert conversation.title == "Repo Test"
            assert conversation.user_id == test_user

    def test_find_by_uuid(self, app, test_user):
        """Test finding a conversation by UUID."""
        from app.database import get_session
        from app.repositories.conversation_repository import ConversationRepository

        with app.app_context():
            session = get_session()
            repo = ConversationRepository(session)

            # Create a conversation
            conversation = repo.create(user_id=test_user, title="Find Test")

            # Find it by UUID
            found = repo.find_by_uuid(conversation.uuid)

            assert found is not None
            assert found.id == conversation.id
            assert found.title == "Find Test"

    def test_find_by_uuid_not_found(self, app):
        """Test finding a non-existent conversation."""
        from app.database import get_session
        from app.repositories.conversation_repository import ConversationRepository

        with app.app_context():
            session = get_session()
            repo = ConversationRepository(session)
            found = repo.find_by_uuid("nonexistent-uuid")

            assert found is None

    def test_find_by_user_with_pagination(self, app, test_user):
        """Test finding conversations by user with pagination."""
        from app.database import get_session
        from app.repositories.conversation_repository import ConversationRepository

        with app.app_context():
            session = get_session()
            repo = ConversationRepository(session)

            # Create multiple conversations
            for i in range(5):
                repo.create(user_id=test_user, title=f"Conversation {i}")

            # Test pagination - returns (conversations, total)
            conversations, total = repo.find_by_user_id(user_id=test_user, page=1, per_page=2)

            assert len(conversations) == 2
            assert total == 5


class TestMessageRepository:
    """Test message repository."""

    def test_create_message(self, app, test_user):
        """Test creating a message through repository."""
        from app.database import get_session
        from app.repositories.conversation_repository import ConversationRepository
        from app.repositories.message_repository import MessageRepository

        with app.app_context():
            session = get_session()

            # Create a conversation first
            conv_repo = ConversationRepository(session)
            conversation = conv_repo.create(user_id=test_user, title="Message Test")

            # Create a message
            msg_repo = MessageRepository(session)
            message = msg_repo.create(
                conversation_id=conversation.id,
                role="user",
                content="Test message content",
            )

            assert message.id is not None
            assert message.role == "user"
            assert message.content == "Test message content"

    def test_find_by_conversation_id(self, app, test_user):
        """Test finding messages by conversation ID."""
        from app.database import get_session
        from app.repositories.conversation_repository import ConversationRepository
        from app.repositories.message_repository import MessageRepository

        with app.app_context():
            session = get_session()

            # Create a conversation
            conv_repo = ConversationRepository(session)
            conversation = conv_repo.create(user_id=test_user, title="Message List Test")

            # Create messages
            msg_repo = MessageRepository(session)
            msg_repo.create(conversation_id=conversation.id, role="user", content="Hello")
            msg_repo.create(conversation_id=conversation.id, role="assistant", content="Hi!")

            # Find messages
            messages = msg_repo.find_by_conversation_id(conversation.id)

            assert len(messages) == 2
            assert messages[0].role == "user"
            assert messages[1].role == "assistant"
