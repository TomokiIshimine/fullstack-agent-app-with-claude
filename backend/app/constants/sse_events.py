"""SSE event constants for streaming responses."""


class SSEEvent:
    """SSE event type names for streaming API responses.

    These constants define the event names used in Server-Sent Events (SSE)
    for conversation streaming endpoints.

    Usage:
        yield f"event: {SSEEvent.CONTENT_DELTA}\\ndata: ...\\n\\n"
    """

    # Conversation creation events
    CONVERSATION_CREATED = "conversation_created"

    # Message lifecycle events
    MESSAGE_START = "message_start"
    MESSAGE_END = "message_end"

    # Content streaming events
    CONTENT_DELTA = "content_delta"

    # Tool execution events
    TOOL_CALL_START = "tool_call_start"
    TOOL_CALL_END = "tool_call_end"

    # Error events
    ERROR = "error"


# Service event type to SSE event type mapping
# Maps internal event types to SSE event names
SERVICE_TO_SSE_EVENT_MAP = {
    "created": SSEEvent.CONVERSATION_CREATED,
    "start": SSEEvent.MESSAGE_START,
    "end": SSEEvent.MESSAGE_END,
    "delta": SSEEvent.CONTENT_DELTA,
    "tool_call_start": SSEEvent.TOOL_CALL_START,
    "tool_call_end": SSEEvent.TOOL_CALL_END,
}


__all__ = ["SSEEvent", "SERVICE_TO_SSE_EVENT_MAP"]
