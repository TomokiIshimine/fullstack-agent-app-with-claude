"""Tests for MetadataService."""

import pytest

from app.services.agent_service import MessageMetadataEvent
from app.services.metadata_service import METADATA_FIELDS, MessageMetadata, MetadataService, StreamingResult, _to_nullable


class TestToNullable:
    """Tests for _to_nullable helper function."""

    def test_returns_value_when_not_empty(self):
        """Should return the original value when is_empty is False."""
        assert _to_nullable(100, is_empty=False) == 100
        assert _to_nullable(3.14, is_empty=False) == 3.14
        assert _to_nullable("test", is_empty=False) == "test"

    def test_returns_none_when_empty(self):
        """Should return None when is_empty is True."""
        assert _to_nullable(100, is_empty=True) is None
        assert _to_nullable(3.14, is_empty=True) is None
        assert _to_nullable("test", is_empty=True) is None


class TestMessageMetadata:
    """Tests for MessageMetadata dataclass."""

    def test_empty_creates_zero_values(self):
        """Should create metadata with all zero/empty values."""
        metadata = MessageMetadata.empty()

        assert metadata.input_tokens == 0
        assert metadata.output_tokens == 0
        assert metadata.model == ""
        assert metadata.response_time_ms == 0
        assert metadata.cost_usd == 0.0

    def test_creates_with_values(self):
        """Should create metadata with provided values."""
        metadata = MessageMetadata(
            input_tokens=100,
            output_tokens=50,
            model="claude-3",
            response_time_ms=500,
            cost_usd=0.01,
        )

        assert metadata.input_tokens == 100
        assert metadata.output_tokens == 50
        assert metadata.model == "claude-3"
        assert metadata.response_time_ms == 500
        assert metadata.cost_usd == 0.01


class TestStreamingResult:
    """Tests for StreamingResult dataclass."""

    def test_to_metadata_converts_correctly(self):
        """Should convert StreamingResult to MessageMetadata."""
        result = StreamingResult(
            content="Hello",
            input_tokens=100,
            output_tokens=50,
            model="claude-3",
            response_time_ms=500,
            cost_usd=0.01,
        )

        metadata = result.to_metadata()

        assert isinstance(metadata, MessageMetadata)
        assert metadata.input_tokens == 100
        assert metadata.output_tokens == 50
        assert metadata.model == "claude-3"
        assert metadata.response_time_ms == 500
        assert metadata.cost_usd == 0.01


class TestMetadataService:
    """Tests for MetadataService."""

    @pytest.fixture
    def service(self):
        """Create a MetadataService instance."""
        return MetadataService()

    class TestHasValidData:
        """Tests for has_valid_data method."""

        @pytest.fixture
        def service(self):
            return MetadataService()

        def test_returns_true_with_input_tokens(self, service):
            """Should return True when input_tokens > 0."""
            metadata = MessageMetadata(
                input_tokens=100,
                output_tokens=0,
                model="",
                response_time_ms=0,
                cost_usd=0.0,
            )
            assert service.has_valid_data(metadata) is True

        def test_returns_true_with_output_tokens(self, service):
            """Should return True when output_tokens > 0."""
            metadata = MessageMetadata(
                input_tokens=0,
                output_tokens=50,
                model="",
                response_time_ms=0,
                cost_usd=0.0,
            )
            assert service.has_valid_data(metadata) is True

        def test_returns_true_with_response_time(self, service):
            """Should return True when response_time_ms > 0."""
            metadata = MessageMetadata(
                input_tokens=0,
                output_tokens=0,
                model="",
                response_time_ms=500,
                cost_usd=0.0,
            )
            assert service.has_valid_data(metadata) is True

        def test_returns_true_with_cost(self, service):
            """Should return True when cost_usd > 0."""
            metadata = MessageMetadata(
                input_tokens=0,
                output_tokens=0,
                model="",
                response_time_ms=0,
                cost_usd=0.01,
            )
            assert service.has_valid_data(metadata) is True

        def test_returns_false_when_all_zero(self, service):
            """Should return False when all values are zero/empty."""
            metadata = MessageMetadata.empty()
            assert service.has_valid_data(metadata) is False

    class TestToNullableDict:
        """Tests for to_nullable_dict method."""

        @pytest.fixture
        def service(self):
            return MetadataService()

        def test_converts_zero_to_none(self, service):
            """Should convert zero values to None."""
            metadata = MessageMetadata.empty()
            result = service.to_nullable_dict(metadata)

            assert result["input_tokens"] is None
            assert result["output_tokens"] is None
            assert result["model"] is None
            assert result["response_time_ms"] is None
            assert result["cost_usd"] is None

        def test_preserves_non_zero_values(self, service):
            """Should preserve non-zero values."""
            metadata = MessageMetadata(
                input_tokens=100,
                output_tokens=50,
                model="claude-3",
                response_time_ms=500,
                cost_usd=0.01,
            )
            result = service.to_nullable_dict(metadata)

            assert result["input_tokens"] == 100
            assert result["output_tokens"] == 50
            assert result["model"] == "claude-3"
            assert result["response_time_ms"] == 500
            assert result["cost_usd"] == 0.01

    class TestBuildFromEvent:
        """Tests for build_from_event method."""

        @pytest.fixture
        def service(self):
            return MetadataService()

        def test_returns_empty_for_none_event(self, service):
            """Should return empty metadata when event is None."""
            result = service.build_from_event(None)

            assert result.input_tokens == 0
            assert result.output_tokens == 0
            assert result.model == ""
            assert result.response_time_ms == 0
            assert result.cost_usd == 0.0

        def test_builds_metadata_from_event(self, service):
            """Should build metadata from valid event."""
            event = MessageMetadataEvent(
                input_tokens=100,
                output_tokens=50,
                model="claude-3",
                response_time_ms=500,
            )
            result = service.build_from_event(event)

            assert result.input_tokens == 100
            assert result.output_tokens == 50
            assert result.model == "claude-3"
            assert result.response_time_ms == 500

        def test_raises_error_for_negative_input_tokens(self, service):
            """Should raise ValueError for negative input_tokens."""
            event = MessageMetadataEvent(
                input_tokens=-1,
                output_tokens=50,
                model="claude-3",
                response_time_ms=500,
            )
            with pytest.raises(ValueError, match="input_tokens cannot be negative"):
                service.build_from_event(event)

        def test_raises_error_for_negative_output_tokens(self, service):
            """Should raise ValueError for negative output_tokens."""
            event = MessageMetadataEvent(
                input_tokens=100,
                output_tokens=-1,
                model="claude-3",
                response_time_ms=500,
            )
            with pytest.raises(ValueError, match="output_tokens cannot be negative"):
                service.build_from_event(event)

        def test_raises_error_for_negative_response_time(self, service):
            """Should raise ValueError for negative response_time_ms."""
            event = MessageMetadataEvent(
                input_tokens=100,
                output_tokens=50,
                model="claude-3",
                response_time_ms=-1,
            )
            with pytest.raises(ValueError, match="response_time_ms cannot be negative"):
                service.build_from_event(event)

    class TestBuildStreamingResult:
        """Tests for build_streaming_result method."""

        @pytest.fixture
        def service(self):
            return MetadataService()

        def test_builds_result_with_content_and_metadata(self, service):
            """Should build StreamingResult with content and metadata."""
            event = MessageMetadataEvent(
                input_tokens=100,
                output_tokens=50,
                model="claude-3",
                response_time_ms=500,
            )
            result = service.build_streaming_result("Hello world", event)

            assert result.content == "Hello world"
            assert result.input_tokens == 100
            assert result.output_tokens == 50
            assert result.model == "claude-3"
            assert result.response_time_ms == 500

        def test_builds_empty_result_for_none_event(self, service):
            """Should build StreamingResult with empty metadata for None event."""
            result = service.build_streaming_result("Hello", None)

            assert result.content == "Hello"
            assert result.input_tokens == 0
            assert result.output_tokens == 0
            assert result.model == ""
            assert result.response_time_ms == 0
            assert result.cost_usd == 0.0

    class TestApplyToMessage:
        """Tests for apply_to_message method."""

        @pytest.fixture
        def service(self):
            return MetadataService()

        def test_applies_metadata_fields_to_message(self, service):
            """Should apply all metadata fields to message model."""

            class MockMessage:
                def __init__(self):
                    for field in METADATA_FIELDS:
                        setattr(self, field, None)

            message = MockMessage()
            metadata = MessageMetadata(
                input_tokens=100,
                output_tokens=50,
                model="claude-3",
                response_time_ms=500,
                cost_usd=0.01,
            )

            service.apply_to_message(message, metadata)

            assert message.input_tokens == 100
            assert message.output_tokens == 50
            assert message.model == "claude-3"
            assert message.response_time_ms == 500
            assert message.cost_usd == 0.01

        def test_applies_none_for_empty_values(self, service):
            """Should apply None for zero/empty values."""

            class MockMessage:
                def __init__(self):
                    for field in METADATA_FIELDS:
                        setattr(self, field, "placeholder")

            message = MockMessage()
            metadata = MessageMetadata.empty()

            service.apply_to_message(message, metadata)

            assert message.input_tokens is None
            assert message.output_tokens is None
            assert message.model is None
            assert message.response_time_ms is None
            assert message.cost_usd is None

    class TestToResponseDict:
        """Tests for to_response_dict method."""

        @pytest.fixture
        def service(self):
            return MetadataService()

        def test_converts_streaming_result_to_response_dict(self, service):
            """Should convert StreamingResult metadata to response dict."""
            result = StreamingResult(
                content="Hello",
                input_tokens=100,
                output_tokens=50,
                model="claude-3",
                response_time_ms=500,
                cost_usd=0.01,
            )

            response = service.to_response_dict(result)

            assert response["input_tokens"] == 100
            assert response["output_tokens"] == 50
            assert response["model"] == "claude-3"
            assert response["response_time_ms"] == 500
            assert response["cost_usd"] == 0.01


class TestMetadataFields:
    """Tests for METADATA_FIELDS constant."""

    def test_contains_expected_fields(self):
        """Should contain all expected metadata field names."""
        expected = ("input_tokens", "output_tokens", "model", "response_time_ms", "cost_usd")
        assert METADATA_FIELDS == expected
