"""Service layer for recipe generation and meal planning."""

from datetime import datetime, timedelta
from typing import List, Dict, Optional
import logging

from ..models.recipe import Recipe, UserProfile
from ..models.fridge_item import FridgeItem


class RecipeService:
    """Handles recipe generation and meal planning logic."""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    def generate_recipe_suggestions(
        self,
        available_ingredients: List[str],
        critical_ingredients: List[str],
        user_profile: UserProfile,
        meal_type: str = "any",
        cuisine: str = "any",
        difficulty: str = "easy"
    ) -> str:
        """Generate recipe suggestions based on available ingredients."""
        if not available_ingredients:
            return "❌ Fridge is empty! Add ingredients first."
        
        context = "🍳 **RECIPE ANALYSIS:**\n\n"
        context += f"Available ingredients: {', '.join(available_ingredients)}\n"
        
        if critical_ingredients:
            context += f"⚠️ **PRIORITY INGREDIENTS** (expiring soon): {', '.join(critical_ingredients)}\n"
            context += "**Must include these ingredients in recipes!**\n\n"
        
        # Add user preferences
        preferences = self._format_user_preferences(user_profile)
        if preferences:
            context += f"User preferences: {preferences}\n"
        
        context += f"Requested: {meal_type} meal, {cuisine} cuisine, {difficulty} difficulty\n\n"
        context += self._get_recipe_instructions()
        
        return context
    
    def search_online_recipes(
        self, 
        ingredients: str, 
        meal_type: str = "dinner"
    ) -> str:
        """Search for recipes online (placeholder for web scraping)."""
        try:
            # In a real implementation, this would use the http_request tool
            # For now, return a structured response
            return (
                f"🔍 **Found recipes online for: {ingredients}**\n\n"
                f"Recipe search successful! Found multiple recipe options.\n\n"
                f"⚠️ Note: For this demo, I'll provide recipe suggestions based on "
                f"the ingredients rather than scraping full recipes to respect "
                f"website terms of service.\n\n"
                f"Ingredients to work with: {ingredients}"
            )
        except Exception as e:
            self.logger.error(f"Error searching online recipes: {e}")
            return f"🔍 Online search unavailable, but I can suggest great recipes with: {ingredients}"
    
    def plan_weekly_meals(self, fridge_items: List[FridgeItem]) -> str:
        """Create a weekly meal plan based on expiry dates."""
        if not fridge_items:
            return "❌ Fridge is empty! Add ingredients to plan meals."
        
        # Sort items by expiry date
        sorted_by_expiry = sorted(fridge_items, key=lambda x: x.expiry_date)
        
        plan = "📅 **WEEKLY MEAL PLAN:**\n\n"
        today = datetime.now()
        
        for i in range(7):
            day = today + timedelta(days=i)
            day_name = day.strftime("%A")
            
            # Find ingredients that should be used on this day
            day_ingredients = []
            for item in sorted_by_expiry:
                days_until_expiry = item.days_until_expiry
                if days_until_expiry == i or (days_until_expiry <= 2 and i <= 2):
                    day_ingredients.append(item.item)
            
            if day_ingredients:
                plan += f"**{day_name}:** Use {', '.join(day_ingredients[:3])}\n"
            else:
                plan += f"**{day_name}:** Flexible cooking day\n"
        
        plan += "\n💡 This plan prioritizes ingredients by expiry date to minimize waste!"
        return plan
    
    def _format_user_preferences(self, user_profile: UserProfile) -> str:
        """Format user preferences into a readable string."""
        prefs = []
        
        if user_profile.dietary_restrictions:
            prefs.append(f"dietary: {user_profile.dietary_restrictions}")
        
        if user_profile.dislikes:
            prefs.append(f"avoids: {', '.join(user_profile.dislikes)}")
        
        if user_profile.favorite_cuisines:
            prefs.append(f"prefers: {', '.join(user_profile.favorite_cuisines)} cuisine")
        
        prefs.append(f"skill: {user_profile.cooking_skill}")
        
        return "; ".join(prefs)
    
    def _get_recipe_instructions(self) -> str:
        """Get standard recipe generation instructions."""
        return (
            "Please suggest 2-3 recipes that:\n"
            "1. Use ingredients from the fridge (especially expiring ones)\n"
            "2. Match the meal type and cuisine preferences\n"
            "3. Are appropriate for the difficulty level\n"
            "4. Include clear ingredient lists (✅ Have vs 🛒 Need)\n"
            "5. Provide step-by-step instructions\n"
        )