"""MCP tool definitions for fridge management."""

from typing import Callable
from ..services.fridge_service import FridgeService


class FridgeTools:
    """Factory for fridge-related MCP tools."""
    
    def __init__(self, fridge_service: FridgeService):
        self.fridge_service = fridge_service
    
    def add_item_tool(self) -> Callable:
        """Create add_item MCP tool."""
        def add_item(item: str, quantity: str = "1", expiry_days: int = 7, notes: str = "") -> str:
            success, message = self.fridge_service.add_item(item, quantity, expiry_days, notes)
            return message
        return add_item
    
    def get_expiring_items_tool(self) -> Callable:
        """Create get_expiring_items MCP tool."""
        def get_expiring_items(days_threshold: int = 3) -> str:
            return self.fridge_service.get_expiring_items(days_threshold)
        return get_expiring_items
    
    def list_items_tool(self) -> Callable:
        """Create list_items MCP tool."""
        def list_items(sort_by: str = "expiry") -> str:
            return self.fridge_service.list_items(sort_by)
        return list_items
    
    def remove_item_tool(self) -> Callable:
        """Create remove_item MCP tool."""
        def remove_item(item: str, amount: str = "all") -> str:
            success, message = self.fridge_service.remove_item(item, amount)
            return message
        return remove_item