"""Agent service for LangGraph ReAct agent integration."""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass
from typing import Any, Generator

from anthropic import APIConnectionError, APIStatusError, RateLimitError
from langchain_core.messages import AIMessage, AIMessageChunk, HumanMessage, ToolMessage
from langgraph.prebuilt import create_react_agent

from app.constants.agent import MAX_CONVERSATION_TITLE_LENGTH, TITLE_TRUNCATION_LENGTH, TITLE_TRUNCATION_SUFFIX
from app.constants.error_types import LLMErrorType
from app.core.exceptions import LLMConnectionError, LLMContextLengthError, LLMRateLimitError, LLMStreamError
from app.providers import BaseLLMProvider, create_provider
from app.tools import ToolRegistry, get_tool_registry

logger = logging.getLogger(__name__)

# System prompt for the AI agent
SYSTEM_PROMPT = """You are a helpful AI assistant. You have access to calculator tools for arithmetic operations.
When the user asks for calculations, use the appropriate tool (add, subtract, multiply, divide).
Please respond in the same language as the user."""


@dataclass
class ToolCallEvent:
    """Event emitted when a tool is called."""

    tool_call_id: str
    tool_name: str
    input: dict[str, Any]


@dataclass
class ToolResultEvent:
    """Event emitted when a tool returns a result."""

    tool_call_id: str
    output: str | None
    error: str | None


@dataclass
class TextDeltaEvent:
    """Event emitted for text content."""

    delta: str


@dataclass
class MessageCompleteEvent:
    """Event emitted when agent response is complete."""

    content: str


@dataclass
class RetryEvent:
    """Event emitted when a retry is attempted."""

    attempt: int
    max_attempts: int
    error_type: str
    delay: float


AgentEvent = ToolCallEvent | ToolResultEvent | TextDeltaEvent | MessageCompleteEvent | RetryEvent


class AgentService:
    """Service for AI agent functionality using LangGraph ReAct pattern.

    This service is initialized with a BaseLLMProvider instance.

    Example:
        from app.providers import create_provider
        provider = create_provider()
        service = AgentService(provider=provider)

        # Or use default provider from environment
        service = AgentService()
    """

    def __init__(
        self,
        provider: BaseLLMProvider | None = None,
        tool_registry: ToolRegistry | None = None,
        system_prompt: str | None = None,
    ) -> None:
        """Initialize agent service with LLM and tools.

        Args:
            provider: LLM provider instance. If None, creates from environment.
            tool_registry: Tool registry instance. If None, uses global registry.
            system_prompt: System prompt override. Defaults to SYSTEM_PROMPT.
        """
        self._system_prompt = system_prompt or SYSTEM_PROMPT

        if provider is not None:
            self._provider = provider
        else:
            self._provider = create_provider()

        self.llm = self._provider.create_chat_model()

        # Get tools from registry
        registry = tool_registry or get_tool_registry()
        self.tools = registry.get_all_tools()

        # Create ReAct agent graph
        self.agent = create_react_agent(
            self.llm,
            tools=self.tools,
            prompt=self._system_prompt,
        )

        logger.info(f"AgentService initialized with {len(self.tools)} tools")

    @property
    def provider(self) -> BaseLLMProvider:
        """Return the LLM provider."""
        return self._provider

    @property
    def provider_name(self) -> str:
        """Return the provider name."""
        return self._provider.provider_name

    @property
    def model_name(self) -> str:
        """Return the model name."""
        return self._provider.model_name

    @property
    def max_tokens(self) -> int:
        """Return max tokens."""
        return self._provider.config.max_tokens

    def _convert_messages(self, messages: list[dict[str, str]]) -> list[HumanMessage | AIMessage]:
        """Convert simple message dicts to LangChain message objects."""
        result: list[HumanMessage | AIMessage] = []
        for msg in messages:
            if msg["role"] == "user":
                result.append(HumanMessage(content=msg["content"]))
            elif msg["role"] == "assistant":
                result.append(AIMessage(content=msg["content"]))
        return result

    def _extract_text_content(self, content: Any) -> str:
        """Extract text content from various message content formats.

        Args:
            content: Message content (str, list of dicts, or list of strings)

        Returns:
            Extracted text content as a single string
        """
        if isinstance(content, str):
            return content
        if isinstance(content, list):
            text_parts = []
            for item in content:
                if isinstance(item, dict) and item.get("type") == "text":
                    text_parts.append(item.get("text", ""))
                elif isinstance(item, str):
                    text_parts.append(item)
            return "".join(text_parts)
        return ""

    def _handle_messages_stream(self, data: tuple[Any, Any]) -> str | None:
        """Handle messages stream mode chunk.

        Only processes AIMessageChunk instances to avoid including tool outputs
        in the assistant's text response.

        Args:
            data: Tuple of (message_chunk, metadata) from messages stream

        Returns:
            Extracted text content or None if no content or non-AI message
        """
        if not isinstance(data, tuple) or len(data) != 2:
            return None

        message_chunk, _ = data
        # Filter to only process AI message chunks, ignoring ToolMessage and other types
        if not isinstance(message_chunk, AIMessageChunk):
            return None
        if hasattr(message_chunk, "content") and message_chunk.content:
            text_content = self._extract_text_content(message_chunk.content)
            return text_content if text_content else None
        return None

    def _handle_updates_stream(
        self,
        data: dict[str, Any],
        emitted_tool_calls: set[str],
    ) -> Generator[ToolCallEvent | ToolResultEvent, None, None]:
        """Handle updates stream mode chunk.

        Args:
            data: Dict containing node outputs
            emitted_tool_calls: Set of already emitted tool call IDs (modified in place)

        Yields:
            ToolCallEvent or ToolResultEvent instances
        """
        for node_name, node_output in data.items():
            if node_name == "agent":
                yield from self._process_agent_node(node_output, emitted_tool_calls)
            elif node_name == "tools":
                yield from self._process_tools_node(node_output)

    def _process_agent_node(
        self,
        node_output: dict[str, Any],
        emitted_tool_calls: set[str],
    ) -> Generator[ToolCallEvent, None, None]:
        """Process agent node output for tool calls.

        Args:
            node_output: Output from agent node
            emitted_tool_calls: Set of already emitted tool call IDs

        Yields:
            ToolCallEvent for each new tool call
        """
        agent_messages = node_output.get("messages", [])
        for msg in agent_messages:
            if hasattr(msg, "tool_calls") and msg.tool_calls:
                for tool_call in msg.tool_calls:
                    tool_call_id = tool_call["id"]
                    if tool_call_id not in emitted_tool_calls:
                        emitted_tool_calls.add(tool_call_id)
                        yield ToolCallEvent(
                            tool_call_id=tool_call_id,
                            tool_name=tool_call["name"],
                            input=tool_call["args"],
                        )

    def _process_tools_node(
        self,
        node_output: dict[str, Any],
    ) -> Generator[ToolResultEvent, None, None]:
        """Process tools node output for results.

        Args:
            node_output: Output from tools node

        Yields:
            ToolResultEvent for each tool result
        """
        tool_messages = node_output.get("messages", [])
        for msg in tool_messages:
            if isinstance(msg, ToolMessage):
                error = None
                output = str(msg.content) if msg.content else None

                if hasattr(msg, "status") and msg.status == "error":
                    error = output
                    output = None

                yield ToolResultEvent(
                    tool_call_id=msg.tool_call_id,
                    output=output,
                    error=error,
                )

    def _generate_response_attempt(
        self,
        messages: list[dict[str, str]],
    ) -> Generator[AgentEvent, None, None]:
        """Single attempt to generate response.

        Args:
            messages: Conversation history as list of dicts with 'role' and 'content'

        Yields:
            AgentEvent instances for tool calls, results, and text content
        """
        langchain_messages = self._convert_messages(messages)
        inputs = {"messages": langchain_messages}

        full_content = ""
        emitted_tool_calls: set[str] = set()
        needs_newline_before_text = False

        # Stream with both modes:
        # - "messages": token-by-token streaming from LLM
        # - "updates": node completion events (tool calls/results)
        for chunk in self.agent.stream(inputs, stream_mode=["messages", "updates"]):
            if not isinstance(chunk, tuple) or len(chunk) != 2:
                continue

            stream_mode, data = chunk

            if stream_mode == "messages":
                text_content = self._handle_messages_stream(data)
                if text_content:
                    # Add newline before text that follows tool result
                    if needs_newline_before_text:
                        text_content = "\n" + text_content
                        needs_newline_before_text = False
                    full_content += text_content
                    yield TextDeltaEvent(delta=text_content)

            elif stream_mode == "updates" and isinstance(data, dict):
                for event in self._handle_updates_stream(data, emitted_tool_calls):
                    yield event
                    # Set flag after tool result to add newline before next text
                    if isinstance(event, ToolResultEvent):
                        needs_newline_before_text = True

        yield MessageCompleteEvent(content=full_content)

    def generate_response(
        self,
        messages: list[dict[str, str]],
        stream: bool = True,  # noqa: ARG002 - kept for API compatibility
    ) -> Generator[AgentEvent, None, None]:
        """
        Generate AI response using the ReAct agent with retry logic.

        Args:
            messages: Conversation history as list of dicts with 'role' and 'content'
            stream: Whether to stream the response (currently always True for agent)

        Yields:
            AgentEvent instances for tool calls, results, text content, and retry events
        """
        logger.debug(f"Generating agent response with {len(messages)} messages")

        # max_retries is the number of retries, so we need max_retries + 1 attempts
        # (1 initial attempt + max_retries retry attempts)
        max_retries = self._provider.config.max_retries
        max_attempts = max_retries + 1
        base_delay = self._provider.config.retry_delay

        for attempt in range(1, max_attempts + 1):
            try:
                yield from self._generate_response_attempt(messages)
                return  # Success, exit retry loop

            except RateLimitError as e:
                retry_after = getattr(e, "retry_after", None)
                if attempt < max_attempts:
                    delay = retry_after or (base_delay * (2 ** (attempt - 1)))
                    logger.warning(f"Rate limit hit, retrying (attempt {attempt}/{max_attempts}), delay={delay}s")
                    yield RetryEvent(
                        attempt=attempt,
                        max_attempts=max_attempts,
                        error_type=LLMErrorType.RATE_LIMIT,
                        delay=delay,
                    )
                    time.sleep(delay)
                else:
                    logger.error(f"Rate limit exceeded after {max_attempts} attempts")
                    raise LLMRateLimitError(retry_after=retry_after)

            except APIConnectionError as e:
                if attempt < max_attempts:
                    delay = base_delay * (2 ** (attempt - 1))
                    logger.warning(f"Connection error, retrying (attempt {attempt}/{max_attempts}), delay={delay}s")
                    yield RetryEvent(
                        attempt=attempt,
                        max_attempts=max_attempts,
                        error_type=LLMErrorType.CONNECTION,
                        delay=delay,
                    )
                    time.sleep(delay)
                else:
                    logger.error(f"Connection error after {max_attempts} attempts: {e}")
                    raise LLMConnectionError(str(e))

            except APIStatusError as e:
                # Check for context length error (400 with specific message)
                if e.status_code == 400 and "context_length" in str(e).lower():
                    logger.error(f"Context length exceeded: {e}")
                    raise LLMContextLengthError()

                # Retry on server errors (500+)
                if e.status_code >= 500 and attempt < max_attempts:
                    delay = base_delay * (2 ** (attempt - 1))
                    logger.warning(f"Server error ({e.status_code}), retrying (attempt {attempt}/{max_attempts})")
                    yield RetryEvent(
                        attempt=attempt,
                        max_attempts=max_attempts,
                        error_type=LLMErrorType.SERVER_ERROR,
                        delay=delay,
                    )
                    time.sleep(delay)
                else:
                    logger.error(f"API error ({e.status_code}) after {attempt} attempts: {e}")
                    raise LLMStreamError(str(e), is_retryable=False)

            except Exception as e:
                # Generic error handling with retry for unknown errors
                logger.error(f"Unexpected error in agent execution: {e}")
                if attempt < max_attempts:
                    delay = base_delay * (2 ** (attempt - 1))
                    logger.warning(f"Retrying after unexpected error (attempt {attempt}/{max_attempts})")
                    yield RetryEvent(
                        attempt=attempt,
                        max_attempts=max_attempts,
                        error_type=LLMErrorType.UNKNOWN,
                        delay=delay,
                    )
                    time.sleep(delay)
                else:
                    raise LLMStreamError(str(e))

    def generate_title(self, first_message: str) -> str:
        """
        Generate a title for a conversation based on the first message.

        Args:
            first_message: The first user message in the conversation

        Returns:
            Generated title (max MAX_CONVERSATION_TITLE_LENGTH characters)
        """
        # Simple approach: truncate the first message
        title = first_message.strip()
        if len(title) > MAX_CONVERSATION_TITLE_LENGTH:
            title = title[:TITLE_TRUNCATION_LENGTH] + TITLE_TRUNCATION_SUFFIX
        return title


__all__ = [
    "AgentService",
    "AgentEvent",
    "ToolCallEvent",
    "ToolResultEvent",
    "TextDeltaEvent",
    "MessageCompleteEvent",
    "RetryEvent",
    "SYSTEM_PROMPT",
]
