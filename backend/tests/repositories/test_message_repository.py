"""Tests for MessageRepository (message data access layer)."""

from __future__ import annotations

import pytest

from app.models.message import Message
from app.repositories.message_repository import MessageRepository


@pytest.fixture
def message_repo(app):
    """Create MessageRepository instance with test database session."""
    from app.database import get_session

    with app.app_context():
        session = get_session()
        yield MessageRepository(session), session


@pytest.fixture
def sample_conversation(app, test_user):
    """Create a sample conversation for testing."""
    from app.database import get_session
    from app.models.conversation import Conversation

    with app.app_context():
        session = get_session()
        conversation = Conversation(user_id=test_user, title="Test Conversation")
        session.add(conversation)
        session.commit()
        conv_id = conversation.id
        session.expunge(conversation)

    return conv_id


class TestMessageRepositoryCreate:
    """Tests for MessageRepository.create method."""

    def test_create_returns_message_instance(self, app, message_repo, sample_conversation):
        """Test that create returns a Message instance."""
        repo, session = message_repo
        with app.app_context():
            result = repo.create(
                conversation_id=sample_conversation,
                role="user",
                content="Hello, world!",
            )

            assert isinstance(result, Message)
            assert result.id is not None

    def test_create_sets_conversation_id(self, app, message_repo, sample_conversation):
        """Test that create sets the conversation_id correctly."""
        repo, session = message_repo
        with app.app_context():
            result = repo.create(
                conversation_id=sample_conversation,
                role="user",
                content="Test message",
            )

            assert result.conversation_id == sample_conversation

    def test_create_sets_role(self, app, message_repo, sample_conversation):
        """Test that create sets the role correctly."""
        repo, session = message_repo
        with app.app_context():
            user_msg = repo.create(
                conversation_id=sample_conversation,
                role="user",
                content="User message",
            )
            assistant_msg = repo.create(
                conversation_id=sample_conversation,
                role="assistant",
                content="Assistant message",
            )

            assert user_msg.role == "user"
            assert assistant_msg.role == "assistant"

    def test_create_sets_content(self, app, message_repo, sample_conversation):
        """Test that create sets the content correctly."""
        repo, session = message_repo
        with app.app_context():
            result = repo.create(
                conversation_id=sample_conversation,
                role="user",
                content="This is the message content",
            )

            assert result.content == "This is the message content"

    def test_create_with_metadata(self, app, message_repo, sample_conversation):
        """Test creating message with optional metadata."""
        repo, session = message_repo
        with app.app_context():
            result = repo.create(
                conversation_id=sample_conversation,
                role="assistant",
                content="Response",
                input_tokens=100,
                output_tokens=50,
                model="claude-3",
                response_time_ms=1500,
                cost_usd=0.005,
            )

            assert result.input_tokens == 100
            assert result.output_tokens == 50
            assert result.model == "claude-3"
            assert result.response_time_ms == 1500
            assert result.cost_usd == 0.005

    def test_create_without_metadata(self, app, message_repo, sample_conversation):
        """Test creating message without optional metadata."""
        repo, session = message_repo
        with app.app_context():
            result = repo.create(
                conversation_id=sample_conversation,
                role="user",
                content="Simple message",
            )

            assert result.input_tokens is None
            assert result.output_tokens is None
            assert result.model is None
            assert result.response_time_ms is None
            assert result.cost_usd is None

    def test_create_sets_created_at(self, app, message_repo, sample_conversation):
        """Test that create sets created_at timestamp."""
        repo, session = message_repo
        with app.app_context():
            result = repo.create(
                conversation_id=sample_conversation,
                role="user",
                content="Test",
            )

            assert result.created_at is not None


class TestMessageRepositoryFindByConversationId:
    """Tests for MessageRepository.find_by_conversation_id method."""

    def test_find_by_conversation_id_empty(self, app, message_repo, sample_conversation):
        """Test finding messages when none exist."""
        repo, session = message_repo
        with app.app_context():
            result = repo.find_by_conversation_id(sample_conversation)

            assert len(result) == 0

    def test_find_by_conversation_id_single_message(self, app, message_repo, sample_conversation):
        """Test finding a single message."""
        repo, session = message_repo
        with app.app_context():
            repo.create(
                conversation_id=sample_conversation,
                role="user",
                content="Test message",
            )

            result = repo.find_by_conversation_id(sample_conversation)

            assert len(result) == 1
            assert result[0].content == "Test message"

    def test_find_by_conversation_id_multiple_messages(self, app, message_repo, sample_conversation):
        """Test finding multiple messages."""
        repo, session = message_repo
        with app.app_context():
            repo.create(conversation_id=sample_conversation, role="user", content="First")
            repo.create(conversation_id=sample_conversation, role="assistant", content="Second")
            repo.create(conversation_id=sample_conversation, role="user", content="Third")

            result = repo.find_by_conversation_id(sample_conversation)

            assert len(result) == 3

    def test_find_by_conversation_id_ordered_by_created_at(self, app, message_repo, sample_conversation):
        """Test that messages are ordered by created_at ascending."""
        from datetime import datetime, timedelta, timezone

        repo, session = message_repo
        with app.app_context():
            # Use explicit timestamps to ensure deterministic ordering
            # (SQLite has only second-resolution timestamps)
            base_time = datetime.now(timezone.utc)
            msg1 = repo.create(conversation_id=sample_conversation, role="user", content="First")
            msg1.created_at = base_time - timedelta(seconds=2)

            msg2 = repo.create(conversation_id=sample_conversation, role="assistant", content="Second")
            msg2.created_at = base_time - timedelta(seconds=1)

            msg3 = repo.create(conversation_id=sample_conversation, role="user", content="Third")
            msg3.created_at = base_time

            session.flush()

            result = repo.find_by_conversation_id(sample_conversation)

            assert result[0].content == "First"
            assert result[1].content == "Second"
            assert result[2].content == "Third"

    def test_find_by_conversation_id_only_matching(self, app, message_repo, sample_conversation, test_user):
        """Test that only messages for the specified conversation are returned."""
        from app.database import get_session
        from app.models.conversation import Conversation

        repo, session = message_repo
        with app.app_context():
            # Create another conversation
            other_conv = Conversation(user_id=test_user, title="Other")
            session.add(other_conv)
            session.flush()

            # Create messages in both conversations
            repo.create(conversation_id=sample_conversation, role="user", content="Conv 1 msg")
            repo.create(conversation_id=other_conv.id, role="user", content="Conv 2 msg")

            result = repo.find_by_conversation_id(sample_conversation)

            assert len(result) == 1
            assert result[0].content == "Conv 1 msg"


class TestMessageRepositoryUpdateMetadata:
    """Tests for MessageRepository.update_metadata method."""

    def test_update_metadata_all_fields(self, app, message_repo, sample_conversation):
        """Test updating all metadata fields."""
        repo, session = message_repo
        with app.app_context():
            message = repo.create(
                conversation_id=sample_conversation,
                role="assistant",
                content="Response",
            )

            result = repo.update_metadata(
                message.id,
                input_tokens=200,
                output_tokens=100,
                model="claude-4",
                response_time_ms=2000,
                cost_usd=0.01,
            )

            assert result is not None
            assert result.input_tokens == 200
            assert result.output_tokens == 100
            assert result.model == "claude-4"
            assert result.response_time_ms == 2000
            assert result.cost_usd == 0.01

    def test_update_metadata_partial_fields(self, app, message_repo, sample_conversation):
        """Test updating only some metadata fields."""
        repo, session = message_repo
        with app.app_context():
            message = repo.create(
                conversation_id=sample_conversation,
                role="assistant",
                content="Response",
                input_tokens=50,
            )

            result = repo.update_metadata(
                message.id,
                output_tokens=25,
            )

            assert result is not None
            assert result.input_tokens == 50  # Unchanged
            assert result.output_tokens == 25  # Updated

    def test_update_metadata_nonexistent_message(self, app, message_repo):
        """Test updating metadata for non-existent message returns None."""
        repo, session = message_repo
        with app.app_context():
            result = repo.update_metadata(
                99999,
                input_tokens=100,
            )

            assert result is None

    def test_update_metadata_preserves_content(self, app, message_repo, sample_conversation):
        """Test that update_metadata does not change content."""
        repo, session = message_repo
        with app.app_context():
            message = repo.create(
                conversation_id=sample_conversation,
                role="assistant",
                content="Original content",
            )

            repo.update_metadata(
                message.id,
                input_tokens=100,
            )

            # Refresh from database
            session.refresh(message)
            assert message.content == "Original content"


class TestMessageRepositoryCountByConversationId:
    """Tests for MessageRepository.count_by_conversation_id method."""

    def test_count_empty_conversation(self, app, message_repo, sample_conversation):
        """Test counting messages in empty conversation."""
        repo, session = message_repo
        with app.app_context():
            result = repo.count_by_conversation_id(sample_conversation)

            assert result == 0

    def test_count_single_message(self, app, message_repo, sample_conversation):
        """Test counting single message."""
        repo, session = message_repo
        with app.app_context():
            repo.create(conversation_id=sample_conversation, role="user", content="Test")

            result = repo.count_by_conversation_id(sample_conversation)

            assert result == 1

    def test_count_multiple_messages(self, app, message_repo, sample_conversation):
        """Test counting multiple messages."""
        repo, session = message_repo
        with app.app_context():
            for i in range(5):
                repo.create(conversation_id=sample_conversation, role="user", content=f"Msg {i}")

            result = repo.count_by_conversation_id(sample_conversation)

            assert result == 5

    def test_count_only_specified_conversation(self, app, message_repo, sample_conversation, test_user):
        """Test that count only counts messages in specified conversation."""
        from app.database import get_session
        from app.models.conversation import Conversation

        repo, session = message_repo
        with app.app_context():
            # Create another conversation
            other_conv = Conversation(user_id=test_user, title="Other")
            session.add(other_conv)
            session.flush()

            # Create messages in both conversations
            repo.create(conversation_id=sample_conversation, role="user", content="Conv 1")
            repo.create(conversation_id=sample_conversation, role="user", content="Conv 1")
            repo.create(conversation_id=other_conv.id, role="user", content="Conv 2")

            result = repo.count_by_conversation_id(sample_conversation)

            assert result == 2


class TestMessageRepositoryDeleteByConversationId:
    """Tests for MessageRepository.delete_by_conversation_id method."""

    def test_delete_empty_conversation(self, app, message_repo, sample_conversation):
        """Test deleting from empty conversation returns 0."""
        repo, session = message_repo
        with app.app_context():
            result = repo.delete_by_conversation_id(sample_conversation)

            assert result == 0

    def test_delete_single_message(self, app, message_repo, sample_conversation):
        """Test deleting single message."""
        repo, session = message_repo
        with app.app_context():
            repo.create(conversation_id=sample_conversation, role="user", content="Test")

            result = repo.delete_by_conversation_id(sample_conversation)

            assert result == 1
            assert repo.count_by_conversation_id(sample_conversation) == 0

    def test_delete_multiple_messages(self, app, message_repo, sample_conversation):
        """Test deleting multiple messages."""
        repo, session = message_repo
        with app.app_context():
            for i in range(3):
                repo.create(conversation_id=sample_conversation, role="user", content=f"Msg {i}")

            result = repo.delete_by_conversation_id(sample_conversation)

            assert result == 3
            assert repo.count_by_conversation_id(sample_conversation) == 0

    def test_delete_only_specified_conversation(self, app, message_repo, sample_conversation, test_user):
        """Test that delete only removes messages from specified conversation."""
        from app.database import get_session
        from app.models.conversation import Conversation

        repo, session = message_repo
        with app.app_context():
            # Create another conversation
            other_conv = Conversation(user_id=test_user, title="Other")
            session.add(other_conv)
            session.flush()

            # Create messages in both conversations
            repo.create(conversation_id=sample_conversation, role="user", content="Conv 1")
            repo.create(conversation_id=other_conv.id, role="user", content="Conv 2")
            repo.create(conversation_id=other_conv.id, role="user", content="Conv 2")

            result = repo.delete_by_conversation_id(sample_conversation)

            assert result == 1
            assert repo.count_by_conversation_id(other_conv.id) == 2

    def test_delete_returns_count_deleted(self, app, message_repo, sample_conversation):
        """Test that delete returns the number of messages deleted."""
        repo, session = message_repo
        with app.app_context():
            for i in range(7):
                repo.create(conversation_id=sample_conversation, role="user", content=f"Msg {i}")

            result = repo.delete_by_conversation_id(sample_conversation)

            assert result == 7


class TestMessageRepositoryIntegration:
    """Integration tests for MessageRepository."""

    def test_full_message_lifecycle(self, app, message_repo, sample_conversation):
        """Test complete message lifecycle: create, read, update, delete."""
        repo, session = message_repo
        with app.app_context():
            # Create
            msg = repo.create(
                conversation_id=sample_conversation,
                role="assistant",
                content="Initial response",
            )
            assert msg.id is not None
            msg_id = msg.id

            # Read
            messages = repo.find_by_conversation_id(sample_conversation)
            assert len(messages) == 1
            assert messages[0].content == "Initial response"

            # Update metadata
            updated = repo.update_metadata(
                msg_id,
                input_tokens=100,
                output_tokens=50,
                model="claude-3",
            )
            assert updated.input_tokens == 100

            # Count
            count = repo.count_by_conversation_id(sample_conversation)
            assert count == 1

            # Delete
            deleted = repo.delete_by_conversation_id(sample_conversation)
            assert deleted == 1

            # Verify deletion
            final_count = repo.count_by_conversation_id(sample_conversation)
            assert final_count == 0

    def test_conversation_with_many_exchanges(self, app, message_repo, sample_conversation):
        """Test handling many message exchanges in a conversation."""
        repo, session = message_repo
        with app.app_context():
            # Simulate 10 exchanges (20 messages)
            for i in range(10):
                repo.create(
                    conversation_id=sample_conversation,
                    role="user",
                    content=f"User message {i}",
                )
                repo.create(
                    conversation_id=sample_conversation,
                    role="assistant",
                    content=f"Assistant response {i}",
                    input_tokens=50 + i,
                    output_tokens=25 + i,
                )

            messages = repo.find_by_conversation_id(sample_conversation)
            assert len(messages) == 20

            # Verify ordering
            assert messages[0].role == "user"
            assert messages[1].role == "assistant"

            # Verify metadata on assistant messages
            assistant_msgs = [m for m in messages if m.role == "assistant"]
            for i, msg in enumerate(assistant_msgs):
                assert msg.input_tokens == 50 + i
