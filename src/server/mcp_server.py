"""MCP Server with all fridge and recipe tools."""

import threading
from mcp.server import FastMCP
from strands_tools import http_request

from ..services.fridge_service import FridgeService
from ..services.recipe_service import RecipeService


def start_advanced_fridge_server(fridge_service: FridgeService, recipe_service: RecipeService):
    """Start enhanced MCP server with expiry management and recipe tools."""
    mcp = FastMCP("Advanced Fridge & Recipe Server")
    
    # === FRIDGE MANAGEMENT TOOLS ===
    @mcp.tool(description="Add food items to the fridge with smart expiry detection")
    def add_item(item: str, quantity: str = "1", expiry_days: int = 7, notes: str = "") -> str:
        """Add food to fridge with enhanced categorization."""
        success, message = fridge_service.add_item(item, quantity, expiry_days, notes)
        return message
    
    @mcp.tool(description="Get items expiring soon with urgency levels")
    def get_expiring_items(days_threshold: int = 3) -> str:
        """Get items expiring soon with priority levels."""
        return fridge_service.get_expiring_items(days_threshold)
    
    @mcp.tool(description="List fridge items with smart sorting")
    def list_items(sort_by: str = "expiry") -> str:
        """List fridge items with advanced sorting options."""
        return fridge_service.list_items(sort_by)
    
    @mcp.tool(description="Remove items from fridge when used")
    def remove_item(item: str, amount: str = "all") -> str:
        """Remove items from fridge."""
        success, message = fridge_service.remove_item(item, amount)
        return message
    
    # === RECIPE & ORCHESTRATION TOOLS ===
    @mcp.tool(description="Get recipe suggestions with expiry prioritization")
    def get_recipe_suggestions(meal_type: str = "any", cuisine: str = "any", difficulty: str = "easy") -> str:
        """Smart recipe suggestions based on fridge contents and expiry."""
        available_ingredients = fridge_service.get_available_ingredients()
        critical_ingredients = fridge_service.get_critical_ingredients()
        
        # For now, create a basic user profile - in full implementation this would come from memory service
        from ..models.recipe import UserProfile
        user_profile = UserProfile()
        
        return recipe_service.generate_recipe_suggestions(
            available_ingredients, critical_ingredients, user_profile, meal_type, cuisine, difficulty
        )
    
    @mcp.tool(description="Search for real recipes online")
    def search_online_recipes(ingredients: str, meal_type: str = "dinner") -> str:
        """Search for real recipes using web requests."""
        return recipe_service.search_online_recipes(ingredients, meal_type)
    
    @mcp.tool(description="Plan meals for the week based on expiry dates")
    def plan_weekly_meals() -> str:
        """Create a weekly meal plan prioritizing expiring ingredients."""
        return recipe_service.plan_weekly_meals(fridge_service.items)
    
    print("🚀 Starting Advanced Fridge & Recipe Server...")
    mcp.run(transport="streamable-http")