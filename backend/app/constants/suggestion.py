"""Constants for suggestion generation."""

import os

# Model configuration
DEFAULT_SUGGESTION_MODEL = "claude-haiku-4-5-20251001"
SUGGESTION_MODEL = os.environ.get("SUGGESTION_MODEL", DEFAULT_SUGGESTION_MODEL)
SUGGESTION_MAX_TOKENS = 1024

# Number of recent messages to include as context
SUGGESTION_MESSAGE_LIMIT = 6

# System prompt for suggestion generation
SUGGESTION_SYSTEM_PROMPT = (
    "You are a helpful assistant that suggests follow-up responses a user might want to send. "
    "Based on the conversation context, generate 3 to 5 short, diverse follow-up messages "
    "that the user could send next. Each suggestion should be concise (1-2 sentences) "
    "and cover different directions or topics the conversation could go. "
    "Respond in the same language as the conversation."
)

# Tool definition for structured output
SUGGESTION_TOOL_NAME = "generate_suggestions"
SUGGESTION_TOOL_DEFINITION = {
    "name": SUGGESTION_TOOL_NAME,
    "description": "Generate follow-up reply suggestions for the user",
    "input_schema": {
        "type": "object",
        "properties": {
            "suggestions": {
                "type": "array",
                "items": {"type": "string"},
                "minItems": 3,
                "maxItems": 5,
                "description": "List of suggested follow-up messages the user might want to send",
            }
        },
        "required": ["suggestions"],
    },
}

__all__ = [
    "DEFAULT_SUGGESTION_MODEL",
    "SUGGESTION_MAX_TOKENS",
    "SUGGESTION_MESSAGE_LIMIT",
    "SUGGESTION_MODEL",
    "SUGGESTION_SYSTEM_PROMPT",
    "SUGGESTION_TOOL_DEFINITION",
    "SUGGESTION_TOOL_NAME",
]
