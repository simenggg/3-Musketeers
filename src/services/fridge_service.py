"""Service layer for fridge management operations."""

from datetime import datetime, timedelta
from typing import List, Optional, Tuple, Dict
import logging

from ..models.fridge_item import FridgeItem


class FridgeService:
    """Handles all fridge-related business logic."""
    
    def __init__(self):
        self.items: List[FridgeItem] = []
        self.logger = logging.getLogger(__name__)
    
    def add_item(
        self, 
        item_name: str, 
        quantity: str = "1", 
        expiry_days: int = 7, 
        notes: str = ""
    ) -> Tuple[bool, str]:
        """
        Add an item to the fridge with smart categorization.
        
        Returns:
            Tuple[bool, str]: (success, message)
        """
        try:
            # Smart categorization
            category = self._categorize_item(item_name)
            
            # Check for existing items and merge if found
            existing_item = self._find_existing_item(item_name)
            if existing_item:
                existing_item.quantity = f"{existing_item.quantity} + {quantity}"
                return True, f"Updated {item_name}: now have {existing_item.quantity}"
            
            # Create new item
            expiry_date = datetime.now() + timedelta(days=expiry_days)
            new_item = FridgeItem(
                item=item_name,
                quantity=quantity,
                category=category,
                expiry_date=expiry_date,
                added=datetime.now(),
                notes=notes
            )
            
            self.items.append(new_item)
            
            # Generate response with urgency warning
            urgency_msg = self._get_urgency_message(expiry_days)
            return True, f"Added {quantity} {item_name} to fridge (expires in {expiry_days} days){urgency_msg}"
            
        except Exception as e:
            self.logger.error(f"Error adding item {item_name}: {e}")
            return False, f"Failed to add {item_name}. Please try again."
    
    def get_expiring_items(self, days_threshold: int = 3) -> str:
        """Get formatted report of expiring items."""
        if not self.items:
            return "No items in fridge"
        
        # Categorize by urgency
        critical, urgent, upcoming = self._categorize_by_urgency()
        
        report = "🚨 **EXPIRY REPORT:**\n\n"
        
        if critical:
            report += "🔴 **CRITICAL - Use Now:**\n"
            for item, status in critical:
                report += f"• {item.quantity} {item.item} ({status})\n"
            report += "\n"
        
        if urgent:
            report += "🟡 **URGENT - Use Soon:**\n"
            for item, status in urgent:
                report += f"• {item.quantity} {item.item} ({status})\n"
            report += "\n"
        
        if upcoming:
            report += "🟢 **UPCOMING:**\n"
            for item, status in upcoming:
                report += f"• {item.quantity} {item.item} ({status})\n"
        
        if not critical and not urgent and not upcoming:
            report += "✅ All items are fresh!"
        
        return report
    
    def list_items(self, sort_by: str = "expiry") -> str:
        """List all fridge items with smart formatting."""
        if not self.items:
            return "Fridge is empty! Add some groceries."
        
        # Sort items
        sorted_items = self._sort_items(sort_by)
        
        result = "🥬 **YOUR FRIDGE:**\n\n"
        current_category = None
        
        for item in sorted_items:
            # Add category headers if sorting by category
            if sort_by == "category" and item.category != current_category:
                current_category = item.category
                result += f"**{current_category.upper()}:**\n"
            
            # Add item with status
            status = self._get_item_status(item)
            result += f"• {item.quantity} {item.item} ({status})\n"
        
        # Add summary
        total = len(self.items)
        expiring_soon = len([i for i in self.items if i.days_until_expiry <= 3])
        result += f"\n📊 Total: {total} items | ⚠️ Expiring soon: {expiring_soon}"
        
        return result
    
    def remove_item(self, item_name: str, amount: str = "all") -> Tuple[bool, str]:
        """Remove an item from the fridge."""
        try:
            matches = self._find_matching_items(item_name)
            
            if not matches:
                return False, f"❌ Couldn't find '{item_name}' in fridge"
            
            if len(matches) > 1:
                items_list = [item.item for item in matches]
                return False, f"🤔 Found multiple items: {', '.join(items_list)}. Be more specific?"
            
            # Remove the item
            item_to_remove = matches[0]
            self.items.remove(item_to_remove)
            
            return True, f"✅ Removed {item_to_remove.quantity} {item_to_remove.item} from fridge"
            
        except Exception as e:
            self.logger.error(f"Error removing item {item_name}: {e}")
            return False, f"Failed to remove {item_name}. Please try again."
    
    def get_available_ingredients(self) -> List[str]:
        """Get list of available ingredient names."""
        return [item.item for item in self.items]
    
    def get_critical_ingredients(self) -> List[str]:
        """Get ingredients that are expiring soon."""
        return [
            item.item for item in self.items 
            if item.urgency_level in ["critical", "urgent"]
        ]
    
    # Private helper methods
    def _categorize_item(self, item_name: str) -> str:
        """Categorize item based on name."""
        categories = {
            'protein': ['chicken', 'beef', 'fish', 'eggs', 'tofu', 'pork', 'turkey', 
                       'salmon', 'tuna', 'shrimp', 'bacon', 'ham'],
            'dairy': ['milk', 'cheese', 'butter', 'yogurt', 'cream', 'sour cream', 
                     'cottage cheese'],
            'vegetable': ['tomato', 'onion', 'carrot', 'spinach', 'lettuce', 'broccoli', 
                         'potato', 'bell pepper', 'cucumber', 'celery', 'garlic', 'ginger'],
            'fruit': ['apple', 'banana', 'orange', 'berry', 'lemon', 'lime', 'avocado', 
                     'strawberry', 'grapes'],
            'grain': ['rice', 'pasta', 'bread', 'flour', 'oats', 'quinoa', 'noodles'],
            'spice': ['salt', 'pepper', 'basil', 'oregano', 'paprika', 'cumin', 'thyme']
        }
        
        item_lower = item_name.lower()
        for category, keywords in categories.items():
            if any(keyword in item_lower for keyword in keywords):
                return category
        return 'misc'
    
    def _find_existing_item(self, item_name: str) -> Optional[FridgeItem]:
        """Find existing item by name (case insensitive)."""
        for item in self.items:
            if item.item.lower() == item_name.lower():
                return item
        return None
    
    def _find_matching_items(self, search_term: str) -> List[FridgeItem]:
        """Find items that match search term."""
        search_lower = search_term.lower()
        return [item for item in self.items if search_lower in item.item.lower()]
    
    def _categorize_by_urgency(self) -> Tuple[List, List, List]:
        """Categorize items by urgency levels."""
        critical = []
        urgent = []
        upcoming = []
        
        for item in self.items:
            days_left = item.days_until_expiry
            
            if days_left < 0:
                critical.append((item, f"expired {abs(days_left)} days ago"))
            elif days_left <= 1:
                critical.append((item, "expires today/tomorrow"))
            elif days_left <= 3:
                urgent.append((item, f"expires in {days_left} days"))
            elif days_left <= 7:
                upcoming.append((item, f"expires in {days_left} days"))
        
        return critical, urgent, upcoming
    
    def _sort_items(self, sort_by: str) -> List[FridgeItem]:
        """Sort items by specified criteria."""
        if sort_by == "expiry":
            return sorted(self.items, key=lambda x: x.expiry_date)
        elif sort_by == "category":
            return sorted(self.items, key=lambda x: (x.category, x.expiry_date))
        elif sort_by == "added":
            return sorted(self.items, key=lambda x: x.added, reverse=True)
        else:
            return self.items.copy()
    
    def _get_item_status(self, item: FridgeItem) -> str:
        """Get formatted status string for an item."""
        days_left = item.days_until_expiry
        
        if days_left < 0:
            return f"❌ expired {abs(days_left)} days ago"
        elif days_left == 0:
            return "⚠️ expires today!"
        elif days_left == 1:
            return "⚠️ expires tomorrow!"
        elif days_left <= 3:
            return f"🟡 {days_left} days left"
        else:
            return f"✅ {days_left} days left"
    
    def _get_urgency_message(self, expiry_days: int) -> str:
        """Get urgency warning message."""
        if expiry_days <= 1:
            return " ⚠️ Use very soon!"
        elif expiry_days <= 3:
            return " 🟡 Use within a few days"
        else:
            return ""