"""Conversation request/response schemas."""

from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, field_validator


class CreateConversationRequest(BaseModel):
    """Request schema for creating a new conversation."""

    message: str

    @field_validator("message")
    @classmethod
    def validate_message(cls, v: str) -> str:
        """Validate message content."""
        if not v or not v.strip():
            raise ValueError("Message is required")
        if len(v) > 32000:
            raise ValueError("Message must be at most 32000 characters")
        return v.strip()


class SendMessageRequest(BaseModel):
    """Request schema for sending a message."""

    content: str

    @field_validator("content")
    @classmethod
    def validate_content(cls, v: str) -> str:
        """Validate message content."""
        if not v or not v.strip():
            raise ValueError("Content is required")
        if len(v) > 32000:
            raise ValueError("Content must be at most 32000 characters")
        return v.strip()


class MessageResponse(BaseModel):
    """Response schema for a message."""

    id: int
    role: Literal["user", "assistant"]
    content: str
    created_at: datetime

    model_config = {"from_attributes": True}


class ConversationResponse(BaseModel):
    """Response schema for a conversation (without messages)."""

    uuid: str
    title: str
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class ConversationWithCountResponse(BaseModel):
    """Response schema for a conversation with message count."""

    uuid: str
    title: str
    message_count: int
    created_at: datetime
    updated_at: datetime


class ConversationDetailResponse(BaseModel):
    """Response schema for conversation with messages."""

    conversation: ConversationResponse
    messages: list[MessageResponse]


class PaginationMeta(BaseModel):
    """Pagination metadata."""

    total: int
    page: int
    per_page: int
    total_pages: int


class ConversationListResponse(BaseModel):
    """Response schema for conversation list."""

    conversations: list[ConversationWithCountResponse]
    meta: PaginationMeta


class CreateConversationResponse(BaseModel):
    """Response schema for creating a new conversation."""

    conversation: ConversationResponse
    message: MessageResponse
    assistant_message: MessageResponse


class SendMessageResponse(BaseModel):
    """Response schema for sending a message (non-streaming)."""

    user_message: MessageResponse
    assistant_message: MessageResponse


__all__ = [
    "CreateConversationRequest",
    "SendMessageRequest",
    "MessageResponse",
    "ConversationResponse",
    "ConversationWithCountResponse",
    "ConversationDetailResponse",
    "ConversationListResponse",
    "PaginationMeta",
    "CreateConversationResponse",
    "SendMessageResponse",
]
