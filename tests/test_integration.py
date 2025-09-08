"""Integration tests for the Recipe Assistant."""

import unittest
from unittest.mock import Mock, patch
from src.services.fridge_service import FridgeService
from src.services.recipe_service import RecipeService
from src.services.memory_service import MemoryService


class TestIntegration(unittest.TestCase):
    """Integration test cases."""
    
    def setUp(self):
        """Set up test services."""
        self.fridge_service = FridgeService()
        self.recipe_service = RecipeService()
        self.memory_service = MemoryService()
    
    def test_full_workflow(self):
        """Test complete workflow from adding items to getting recipes."""
        # Add items to fridge
        self.fridge_service.add_item("tomato", "3", 2)  # Expiring soon
        self.fridge_service.add_item("pasta", "1", 10)  # Fresh
        self.fridge_service.add_item("onion", "2", 5)   # Medium
        
        # Get available and critical ingredients
        available = self.fridge_service.get_available_ingredients()
        critical = self.fridge_service.get_critical_ingredients()
        
        # Verify ingredients
        self.assertEqual(set(available), {"tomato", "pasta", "onion"})
        self.assertIn("tomato", critical)  # Should be critical due to 2-day expiry
        
        # Generate recipe suggestions
        user_profile = self.memory_service.user_profile
        recipe_context = self.recipe_service.generate_recipe_suggestions(
            available, critical, user_profile
        )
        
        # Verify recipe context includes critical ingredients
        self.assertIn("tomato", recipe_context)
        self.assertIn("PRIORITY INGREDIENTS", recipe_context)
        
        # Test memory updates
        self.memory_service.add_cooking_session("recipe request", len(recipe_context))
        self.memory_service.add_recipe("Tomato Pasta", "make pasta", recipe_context)
        
        # Verify memory tracking
        self.assertEqual(len(self.memory_service.user_profile.cooking_history), 1)
        self.assertEqual(len(self.memory_service.user_profile.previous_recipes), 1)
    
    def test_expiry_workflow(self):
        """Test expiry management workflow."""
        # Add items with different expiry dates
        self.fridge_service.add_item("expired_item", "1", -1)
        self.fridge_service.add_item("critical_item", "1", 0)
        self.fridge_service.add_item("urgent_item", "1", 2)
        self.fridge_service.add_item("fresh_item", "1", 7)
        
        # Get expiry report
        report = self.fridge_service.get_expiring_items()
        
        # Verify report structure
        self.assertIn("CRITICAL", report)
        self.assertIn("urgent", report)
        
        # Get meal plan
        meal_plan = self.recipe_service.plan_weekly_meals(self.fridge_service.items)
        
        # Verify meal plan prioritizes expiring items
        self.assertIn("WEEKLY MEAL PLAN", meal_plan)
        self.assertIn("expired_item", meal_plan)
