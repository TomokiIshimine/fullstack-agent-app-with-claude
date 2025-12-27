"""Agent service for LangGraph ReAct agent integration."""

from __future__ import annotations

import logging
import os
from dataclasses import dataclass
from typing import Any, Generator

from langchain_anthropic import ChatAnthropic
from langchain_core.messages import AIMessage, HumanMessage, ToolMessage
from langgraph.prebuilt import create_react_agent

from app.tools import get_tool_registry

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


AgentEvent = ToolCallEvent | ToolResultEvent | TextDeltaEvent | MessageCompleteEvent


class AgentService:
    """Service for AI agent functionality using LangGraph ReAct pattern."""

    def __init__(self) -> None:
        """Initialize agent service with LLM and tools."""
        self.provider = os.getenv("LLM_PROVIDER", "anthropic")
        self.model_name = os.getenv("LLM_MODEL", "claude-sonnet-4-5-20250929")
        self.max_tokens = int(os.getenv("CLAUDE_MAX_TOKENS", "4096"))

        # Initialize LLM based on provider
        self.llm = self._create_llm()

        # Get tools from registry
        registry = get_tool_registry()
        self.tools = registry.get_all_tools()

        # Create ReAct agent graph
        self.agent = create_react_agent(
            self.llm,
            tools=self.tools,
            prompt=SYSTEM_PROMPT,
        )

        logger.info(f"AgentService initialized with {len(self.tools)} tools")

    def _create_llm(self) -> ChatAnthropic:
        """Create LLM instance based on provider configuration."""
        if self.provider == "anthropic":
            return ChatAnthropic(
                model=self.model_name,
                max_tokens=self.max_tokens,
                streaming=True,
            )
        else:
            # Future: Add support for other providers
            raise ValueError(f"Unsupported LLM provider: {self.provider}")

    def _convert_messages(self, messages: list[dict[str, str]]) -> list[HumanMessage | AIMessage]:
        """Convert simple message dicts to LangChain message objects."""
        result: list[HumanMessage | AIMessage] = []
        for msg in messages:
            if msg["role"] == "user":
                result.append(HumanMessage(content=msg["content"]))
            elif msg["role"] == "assistant":
                result.append(AIMessage(content=msg["content"]))
        return result

    def generate_response(
        self,
        messages: list[dict[str, str]],
        stream: bool = True,  # noqa: ARG002 - kept for API compatibility
    ) -> Generator[AgentEvent, None, None]:
        """
        Generate AI response using the ReAct agent.

        Args:
            messages: Conversation history as list of dicts with 'role' and 'content'
            stream: Whether to stream the response (currently always True for agent)

        Yields:
            AgentEvent instances for tool calls, results, and text content
        """
        logger.debug(f"Generating agent response with {len(messages)} messages")

        # Convert messages to LangChain format
        langchain_messages = self._convert_messages(messages)
        inputs = {"messages": langchain_messages}

        # Track accumulated content for final message
        full_content = ""

        # Stream agent execution
        try:
            for chunk in self.agent.stream(inputs, stream_mode="updates"):
                # Process each node's output
                for node_name, node_output in chunk.items():
                    if node_name == "agent":
                        # LLM response - may contain tool calls or text
                        agent_messages = node_output.get("messages", [])
                        for msg in agent_messages:
                            if hasattr(msg, "tool_calls") and msg.tool_calls:
                                # Emit tool call events
                                for tool_call in msg.tool_calls:
                                    yield ToolCallEvent(
                                        tool_call_id=tool_call["id"],
                                        tool_name=tool_call["name"],
                                        input=tool_call["args"],
                                    )
                            elif hasattr(msg, "content") and msg.content:
                                # Text content
                                if isinstance(msg.content, str):
                                    full_content = msg.content
                                    yield TextDeltaEvent(delta=msg.content)

                    elif node_name == "tools":
                        # Tool execution results
                        tool_messages = node_output.get("messages", [])
                        for msg in tool_messages:
                            if isinstance(msg, ToolMessage):
                                error = None
                                output = str(msg.content) if msg.content else None

                                # Check for error in tool response
                                if hasattr(msg, "status") and msg.status == "error":
                                    error = output
                                    output = None

                                yield ToolResultEvent(
                                    tool_call_id=msg.tool_call_id,
                                    output=output,
                                    error=error,
                                )

            # Emit final message complete event
            yield MessageCompleteEvent(content=full_content)

        except Exception as e:
            logger.error(f"Error in agent execution: {e}")
            raise

    def generate_title(self, first_message: str) -> str:
        """
        Generate a title for a conversation based on the first message.

        Args:
            first_message: The first user message in the conversation

        Returns:
            Generated title (max 50 characters)
        """
        # Simple approach: truncate the first message
        title = first_message.strip()
        if len(title) > 50:
            title = title[:47] + "..."
        return title


__all__ = [
    "AgentService",
    "AgentEvent",
    "ToolCallEvent",
    "ToolResultEvent",
    "TextDeltaEvent",
    "MessageCompleteEvent",
    "SYSTEM_PROMPT",
]
