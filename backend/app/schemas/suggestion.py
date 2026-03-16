"""Suggestion response schemas."""

from __future__ import annotations

from pydantic import BaseModel


class SuggestionsResponse(BaseModel):
    """Response schema for suggestion generation."""

    suggestions: list[str] = []


__all__ = ["SuggestionsResponse"]
