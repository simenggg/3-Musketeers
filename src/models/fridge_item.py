"""Data models for fridge items and related structures."""

from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from dataclasses import dataclass


@dataclass
class FridgeItem:
    """Represents an item in the fridge with expiry tracking."""
    
    item: str
    quantity: str
    category: str
    expiry_date: datetime
    added: datetime
    notes: str = ""
    
    @property
    def days_until_expiry(self) -> int:
        """Calculate days until expiry (negative if expired)."""
        return (self.expiry_date - datetime.now()).days
    
    @property
    def urgency_level(self) -> str:
        """Get urgency level based on expiry."""
        days = self.days_until_expiry
        if days < 0:
            return "expired"
        elif days <= 1:
            return "critical"
        elif days <= 3:
            return "urgent"
        elif days <= 7:
            return "upcoming"
        else:
            return "fresh"
    
    @property
    def urgency_emoji(self) -> str:
        """Get emoji for urgency level."""
        urgency_map = {
            "expired": "❌",
            "critical": "🔴",
            "urgent": "🟡",
            "upcoming": "🟢",
            "fresh": "✅"
        }
        return urgency_map.get(self.urgency_level, "❓")
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            'item': self.item,
            'quantity': self.quantity,
            'category': self.category,
            'expiry_date': self.expiry_date.isoformat(),
            'added': self.added.isoformat(),
            'notes': self.notes
        }