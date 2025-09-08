"""Unit tests for FridgeService."""

import unittest
from datetime import datetime, timedelta
from src.services.fridge_service import FridgeService
from src.models.fridge_item import FridgeItem


class TestFridgeService(unittest.TestCase):
    """Test cases for FridgeService."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.service = FridgeService()
    
    def test_add_item_success(self):
        """Test successful item addition."""
        success, message = self.service.add_item("tomato", "2", 5)
        
        self.assertTrue(success)
        self.assertIn("tomato", message)
        self.assertEqual(len(self.service.items), 1)
        self.assertEqual(self.service.items[0].category, "vegetable")
    
    def test_add_duplicate_item_merges(self):
        """Test that duplicate items are merged."""
        self.service.add_item("apple", "3", 7)
        success, message = self.service.add_item("apple", "2", 7)
        
        self.assertTrue(success)
        self.assertIn("Updated", message)
        self.assertEqual(len(self.service.items), 1)
    
    def test_categorize_item(self):
        """Test item categorization."""
        self.assertEqual(self.service._categorize_item("chicken"), "protein")
        self.assertEqual(self.service._categorize_item("milk"), "dairy")
        self.assertEqual(self.service._categorize_item("tomato"), "vegetable")
        self.assertEqual(self.service._categorize_item("unknown_item"), "misc")
    
    def test_expiring_items_report(self):
        """Test expiring items report generation."""
        # Add items with different expiry dates
        self.service.add_item("expired_item", "1", -1)
        self.service.add_item("critical_item", "1", 1)
        self.service.add_item("urgent_item", "1", 3)
        self.service.add_item("fresh_item", "1", 10)
        
        report = self.service.get_expiring_items()
        
        self.assertIn("CRITICAL", report)
        self.assertIn("URGENT", report)
        self.assertIn("expired_item", report)
        self.assertIn("critical_item", report)
    
    def test_remove_item_success(self):
        """Test successful item removal."""
        self.service.add_item("banana", "3", 5)
        success, message = self.service.remove_item("banana")
        
        self.assertTrue(success)
        self.assertIn("Removed", message)
        self.assertEqual(len(self.service.items), 0)
    
    def test_remove_nonexistent_item(self):
        """Test removing non-existent item."""
        success, message = self.service.remove_item("nonexistent")
        
        self.assertFalse(success)
        self.assertIn("Couldn't find", message)
    
    def test_list_items_empty_fridge(self):
        """Test listing items when fridge is empty."""
        result = self.service.list_items()
        self.assertIn("empty", result.lower())
    
    def test_get_available_ingredients(self):
        """Test getting available ingredients list."""
        self.service.add_item("onion", "2", 5)
        self.service.add_item("garlic", "1", 10)
        
        ingredients = self.service.get_available_ingredients()
        self.assertEqual(set(ingredients), {"onion", "garlic"})
    
    def test_get_critical_ingredients(self):
        """Test getting critical ingredients."""
        self.service.add_item("expiring_soon", "1", 1)
        self.service.add_item("fresh_item", "1", 10)
        
        critical = self.service.get_critical_ingredients()
        self.assertIn("expiring_soon", critical)
        self.assertNotIn("fresh_item", critical)


class TestFridgeItem(unittest.TestCase):
    """Test cases for FridgeItem model."""
    
    def test_days_until_expiry(self):
        """Test days until expiry calculation."""
        future_date = datetime.now() + timedelta(days=5)
        item = FridgeItem(
            item="test",
            quantity="1",
            category="misc",
            expiry_date=future_date,
            added=datetime.now()
        )
        
        self.assertIn(item.days_until_expiry, [4, 5])
    
    def test_urgency_level(self):
        """Test urgency level calculation."""
        # Test critical item
        critical_date = datetime.now() + timedelta(days=1)
        critical_item = FridgeItem(
            item="critical", quantity="1", category="misc",
            expiry_date=critical_date, added=datetime.now()
        )
        self.assertEqual(critical_item.urgency_level, "critical")
        
        # Test urgent item
        urgent_date = datetime.now() + timedelta(days=3)
        urgent_item = FridgeItem(
            item="urgent", quantity="1", category="misc",
            expiry_date=urgent_date, added=datetime.now()
        )
        self.assertEqual(urgent_item.urgency_level, "urgent")
        
        # Test fresh item
        fresh_date = datetime.now() + timedelta(days=10)
        fresh_item = FridgeItem(
            item="fresh", quantity="1", category="misc",
            expiry_date=fresh_date, added=datetime.now()
        )
        self.assertEqual(fresh_item.urgency_level, "fresh")
