"""MCP tool definitions for recipe management."""

from typing import Callable
from ..services.fridge_service import FridgeService
from ..services.recipe_service import RecipeService
from ..models.recipe import UserProfile


class RecipeTools:
    """Factory for recipe-related MCP tools."""
    
    def __init__(self, fridge_service: FridgeService, recipe_service: RecipeService):
        self.fridge_service = fridge_service
        self.recipe_service = recipe_service
    
    def get_recipe_suggestions_tool(self) -> Callable:
        """Create get_recipe_suggestions MCP tool."""
        def get_recipe_suggestions(meal_type: str = "any", cuisine: str = "any", difficulty: str = "easy") -> str:
            available_ingredients = self.fridge_service.get_available_ingredients()
            critical_ingredients = self.fridge_service.get_critical_ingredients()
            
            # In full implementation, this would come from memory service
            user_profile = UserProfile()
            
            return self.recipe_service.generate_recipe_suggestions(
                available_ingredients, critical_ingredients, user_profile, meal_type, cuisine, difficulty
            )
        return get_recipe_suggestions
    
    def search_online_recipes_tool(self) -> Callable:
        """Create search_online_recipes MCP tool."""
        def search_online_recipes(ingredients: str, meal_type: str = "dinner") -> str:
            return self.recipe_service.search_online_recipes(ingredients, meal_type)
        return search_online_recipes
    
    def plan_weekly_meals_tool(self) -> Callable:
        """Create plan_weekly_meals MCP tool."""
        def plan_weekly_meals() -> str:
            return self.recipe_service.plan_weekly_meals(self.fridge_service.items)
        return plan_weekly_meals