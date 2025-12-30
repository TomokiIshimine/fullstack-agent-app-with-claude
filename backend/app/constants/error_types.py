"""LLM error type constants for error responses."""


class LLMErrorType:
    """LLM error type identifiers for API error responses.

    These constants define the error types used in SSE error events
    and error responses for LLM-related failures.

    Usage:
        error_data = {
            "error": str(exc),
            "error_type": LLMErrorType.RATE_LIMIT,
            "is_retryable": False,
        }
    """

    # Rate limiting error (HTTP 429)
    RATE_LIMIT = "rate_limit"

    # Connection/network error
    CONNECTION = "connection"

    # Server error (HTTP 5xx)
    SERVER_ERROR = "server_error"

    # Context length exceeded
    CONTEXT_LENGTH = "context_length"

    # Streaming error during response
    STREAM_ERROR = "stream_error"

    # Provider configuration/API key error
    PROVIDER_ERROR = "provider_error"

    # Conversation access/not found error
    CONVERSATION_ERROR = "conversation_error"

    # Unknown/generic error
    UNKNOWN = "unknown"


__all__ = ["LLMErrorType"]
