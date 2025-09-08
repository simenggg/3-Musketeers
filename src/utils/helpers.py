"""Utility functions and helpers."""

import re
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta


class ValidationError(Exception):
    """Custom exception for validation errors."""
    pass


def validate_expiry_days(days: int) -> int:
    """Validate and normalize expiry days."""
    if not isinstance(days, int):
        try:
            days = int(days)
        except (ValueError, TypeError):
            raise ValidationError("Expiry days must be a number")
    
    if days < 0:
        raise ValidationError("Expiry days cannot be negative")
    
    if days > 365:
        raise ValidationError("Expiry days cannot exceed 365")
    
    return days


def validate_item_name(item_name: str) -> str:
    """Validate and clean item name."""
    if not isinstance(item_name, str):
        raise ValidationError("Item name must be a string")
    
    cleaned = item_name.strip()
    if not cleaned:
        raise ValidationError("Item name cannot be empty")
    
    if len(cleaned) > 100:
        raise ValidationError("Item name too long (max 100 characters)")
    
    # Remove extra whitespace
    cleaned = re.sub(r'\s+', ' ', cleaned)
    
    return cleaned


def validate_quantity(quantity: str) -> str:
    """Validate and clean quantity string."""
    if not isinstance(quantity, str):
        quantity = str(quantity)
    
    cleaned = quantity.strip()
    if not cleaned:
        return "1"
    
    if len(cleaned) > 50:
        raise ValidationError("Quantity string too long (max 50 characters)")
    
    return cleaned


def parse_ingredients_list(ingredients_text: str) -> List[str]:
    """Parse a comma-separated string of ingredients."""
    if not ingredients_text:
        return []
    
    ingredients = [item.strip() for item in ingredients_text.split(',')]
    return [item for item in ingredients if item]  # Remove empty strings


def format_time_ago(timestamp: datetime) -> str:
    """Format timestamp as human-readable time ago."""
    now = datetime.now()
    diff = now - timestamp
    
    if diff.days > 0:
        return f"{diff.days} day{'s' if diff.days != 1 else ''} ago"
    elif diff.seconds > 3600:
        hours = diff.seconds // 3600
        return f"{hours} hour{'s' if hours != 1 else ''} ago"
    elif diff.seconds > 60:
        minutes = diff.seconds // 60
        return f"{minutes} minute{'s' if minutes != 1 else ''} ago"
    else:
        return "Just now"


def safe_get_nested(data: Dict[str, Any], path: str, default: Any = None) -> Any:
    """Safely get nested dictionary value using dot notation."""
    try:
        keys = path.split('.')
        value = data
        for key in keys:
            value = value[key]
        return value
    except (KeyError, TypeError):
        return default


def truncate_text(text: str, max_length: int, suffix: str = "...") -> str:
    """Truncate text to maximum length with suffix."""
    if len(text) <= max_length:
        return text
    return text[:max_length - len(suffix)] + suffix