"""Date filter utilities for query filtering."""

from __future__ import annotations

from datetime import datetime, time


def parse_date_filter(date_str: str, end_of_day: bool = False) -> datetime | None:
    """Parse date string for filtering, optionally normalizing to end of day.

    Args:
        date_str: ISO format date string (e.g., "2025-01-01" or "2025-01-01T10:00:00Z")
        end_of_day: If True and input is date-only, normalize to 23:59:59.999999

    Returns:
        Parsed datetime or None if parsing fails
    """
    try:
        dt = datetime.fromisoformat(date_str.replace("Z", "+00:00"))
        # If date-only (time is midnight and no explicit time in input),
        # normalize to end of day for inclusive filtering
        if end_of_day and dt.time() == time(0, 0, 0) and "T" not in date_str:
            dt = dt.replace(hour=23, minute=59, second=59, microsecond=999999)
        return dt
    except ValueError:
        return None


__all__ = ["parse_date_filter"]
