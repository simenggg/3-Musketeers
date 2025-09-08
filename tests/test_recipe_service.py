"""Unit tests for RecipeService."""

import unittest
from src.services.recipe_service import RecipeService
from src.models.recipe import UserProfile
from src.models.fridge_item import FridgeItem
from datetime import datetime, timedelta


class TestRecipeService(unittest.TestCase):
    """Test cases for RecipeService."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.service = RecipeService()
        self.user_profile = UserProfile(
            dietary_restrictions="vegetarian",
            dislikes=["mushrooms"],
            favorite_cuisines=["Italian", "Asian"],
            cooking_skill="intermediate"
        )
    
    def test_generate_recipe_suggestions_empty_ingredients(self):
        """Test recipe suggestions with empty ingredients."""
        result = self.service.generate_recipe_suggestions(
            [], [], self.user_profile
        )
        self.assertIn("empty", result.lower())
    
    def test_generate_recipe_suggestions_with_ingredients(self):
        """Test recipe suggestions with available ingredients."""
        available = ["tomato", "onion", "pasta"]
        critical = ["tomato"]
        
        result = self.service.generate_recipe_suggestions(
            available, critical, self.user_profile
        )
        
        self.assertIn("tomato", result)
        self.assertIn("PRIORITY INGREDIENTS", result)
        self.assertIn("vegetarian", result)
    
    def test_format_user_preferences(self):
        """Test user preferences formatting."""
        formatted = self.service._format_user_preferences(self.user_profile)
        
        self.assertIn("dietary: vegetarian", formatted)
        self.assertIn("avoids: mushrooms", formatted)
        self.assertIn("prefers: Italian, Asian cuisine", formatted)
        self.assertIn("skill: intermediate", formatted)
    
    def test_search_online_recipes(self):
        """Test online recipe search."""
        result = self.service.search_online_recipes("tomato pasta", "dinner")
        
        self.assertIn("Found recipes", result)
        self.assertIn("tomato pasta", result)
    
    def test_plan_weekly_meals_empty_fridge(self):
        """Test weekly meal planning with empty fridge."""
        result = self.service.plan_weekly_meals([])
        self.assertIn("empty", result.lower())
    
    def test_plan_weekly_meals_with_items(self):
        """Test weekly meal planning with fridge items."""
        # Create test items with different expiry dates
        items = [
            FridgeItem(
                item="expiring_soon",
                quantity="1",
                category="vegetable",
                expiry_date=datetime.now() + timedelta(days=1),
                added=datetime.now()
            ),
            FridgeItem(
                item="fresh_item",
                quantity="1",
                category="fruit",
                expiry_date=datetime.now() + timedelta(days=10),
                added=datetime.now()
            )
        ]
        
        result = self.service.plan_weekly_meals(items)
        
        self.assertIn("WEEKLY MEAL PLAN", result)
        self.assertIn("expiring_soon", result)
