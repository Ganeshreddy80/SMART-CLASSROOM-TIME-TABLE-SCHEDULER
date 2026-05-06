"""
utils/date_helpers.py — Shared date parsing and formatting utilities.
"""
from datetime import datetime, date as date_type


def parse_date(date_str: str, fmt: str = '%Y-%m-%d') -> date_type:
    """Parse a date string into a date object."""
    if not date_str or not isinstance(date_str, str):
        raise ValueError("Date string must be a non-empty string")
    try:
        parsed = datetime.strptime(date_str, fmt)
        return parsed.date()
    except ValueError:
        raise ValueError(f"Invalid date format '{date_str}'. Expected format: {fmt}")


def parse_iso_date(date_str: str) -> date_type:
    """Parse an ISO format date string (YYYY-MM-DD) into a date object."""
    if not date_str or not isinstance(date_str, str):
        raise ValueError("Date string must be a non-empty string")
    try:
        return date_type.fromisoformat(date_str)
    except ValueError:
        raise ValueError(f"Invalid ISO date format '{date_str}'. Expected YYYY-MM-DD")
