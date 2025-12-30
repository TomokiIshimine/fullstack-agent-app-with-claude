"""Rate limiting constants."""

# Default rate limits
DEFAULT_RATE_LIMITS = ["200 per hour", "50 per minute"]

# Auth endpoint rate limits
LOGIN_RATE_LIMIT = "10 per minute"
REFRESH_RATE_LIMIT = "30 per minute"
LOGOUT_RATE_LIMIT = "20 per minute"

# Conversation endpoint rate limits
CREATE_CONVERSATION_RATE_LIMIT = "30/minute"
SEND_MESSAGE_RATE_LIMIT = "30/minute"

# Rate limit strategy
DEFAULT_RATE_LIMIT_STRATEGY = "fixed-window"

__all__ = [
    "DEFAULT_RATE_LIMITS",
    "LOGIN_RATE_LIMIT",
    "REFRESH_RATE_LIMIT",
    "LOGOUT_RATE_LIMIT",
    "CREATE_CONVERSATION_RATE_LIMIT",
    "SEND_MESSAGE_RATE_LIMIT",
    "DEFAULT_RATE_LIMIT_STRATEGY",
]
