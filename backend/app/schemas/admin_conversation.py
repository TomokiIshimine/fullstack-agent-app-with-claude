"""Admin conversation request/response schemas."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel

from app.schemas.conversation import MessageResponse, PaginationMeta


class AdminUserInfo(BaseModel):
    """User info for admin conversation list."""

    id: int
    email: str
    name: str | None

    model_config = {"from_attributes": True}


class AdminConversationResponse(BaseModel):
    """Response schema for a conversation in admin list."""

    uuid: str
    title: str
    message_count: int
    user: AdminUserInfo
    created_at: datetime
    updated_at: datetime


class AdminConversationListResponse(BaseModel):
    """Response schema for admin conversation list."""

    conversations: list[AdminConversationResponse]
    meta: PaginationMeta


class AdminConversationDetailResponse(BaseModel):
    """Response schema for admin conversation detail."""

    uuid: str
    title: str
    user: AdminUserInfo
    messages: list[MessageResponse]
    created_at: datetime
    updated_at: datetime


__all__ = [
    "AdminUserInfo",
    "AdminConversationResponse",
    "AdminConversationListResponse",
    "AdminConversationDetailResponse",
]
