"""Service layer for user memory and learning capabilities."""

from datetime import datetime
from typing import Dict, List, Any
import logging

from ..models.recipe import UserProfile


class MemoryService:
    """Handles user preferences, learning, and memory management."""
    
    def __init__(self):
        self.user_profile = UserProfile()
        self.logger = logging.getLogger(__name__)
        self._initialize_memory_limits()
    
    def _initialize_memory_limits(self):
        """Set memory size limits to prevent unbounded growth."""
        self.MAX_COOKING_HISTORY = 50
        self.MAX_PREVIOUS_RECIPES = 20
    
    def update_profile(
        self,
        dietary_restrictions: str = None,
        dislikes: List[str] = None,
        favorite_cuisines: List[str] = None,
        cooking_skill: str = None
    ) -> bool:
        """Update user profile with new preferences."""
        try:
            if dietary_restrictions is not None:
                self.user_profile.dietary_restrictions = dietary_restrictions
            
            if dislikes is not None:
                self.user_profile.dislikes = dislikes
            
            if favorite_cuisines is not None:
                self.user_profile.favorite_cuisines = favorite_cuisines
            
            if cooking_skill is not None:
                self.user_profile.cooking_skill = cooking_skill
            
            return True
        except Exception as e:
            self.logger.error(f"Error updating profile: {e}")
            return False
    
    def add_cooking_session(self, request: str, response_length: int) -> None:
        """Record a cooking session for learning purposes."""
        try:
            session = {
                "request": request,
                "response_length": response_length,
                "timestamp": datetime.now().isoformat()
            }
            
            self.user_profile.cooking_history.append(session)
            
            # Limit memory size
            if len(self.user_profile.cooking_history) > self.MAX_COOKING_HISTORY:
                self.user_profile.cooking_history = self.user_profile.cooking_history[-25:]
                
        except Exception as e:
            self.logger.error(f"Error adding cooking session: {e}")
    
    def add_recipe(self, recipe_name: str, user_request: str, full_recipe: str) -> None:
        """Record a recipe suggestion for future reference."""
        try:
            # Truncate long recipes
            truncated_recipe = full_recipe[:300] + "..." if len(full_recipe) > 300 else full_recipe
            
            recipe_record = {
                "name": recipe_name,
                "timestamp": datetime.now().isoformat(),
                "user_request": user_request,
                "full_recipe": truncated_recipe
            }
            
            self.user_profile.previous_recipes.append(recipe_record)
            
            # Limit memory size
            if len(self.user_profile.previous_recipes) > self.MAX_PREVIOUS_RECIPES:
                self.user_profile.previous_recipes = self.user_profile.previous_recipes[-10:]
                
        except Exception as e:
            self.logger.error(f"Error adding recipe: {e}")
    
    def get_memory_context(self) -> str:
        """Generate memory context string for the AI agent."""
        context_parts = []
        
        if self.user_profile.dietary_restrictions:
            context_parts.append(f"Dietary: {self.user_profile.dietary_restrictions}")
        
        if self.user_profile.dislikes:
            context_parts.append(f"Avoids: {', '.join(self.user_profile.dislikes)}")
        
        if self.user_profile.favorite_cuisines:
            context_parts.append(f"Prefers: {', '.join(self.user_profile.favorite_cuisines)} cuisine")
        
        context_parts.append(f"Skill: {self.user_profile.cooking_skill}")
        
        return ". ".join(context_parts) + ". " if context_parts else ""
    
    def get_profile_summary(self) -> Dict[str, Any]:
        """Get a summary of the user profile for display."""
        return {
            "dietary_restrictions": self.user_profile.dietary_restrictions,
            "dislikes": self.user_profile.dislikes,
            "favorite_cuisines": self.user_profile.favorite_cuisines,
            "cooking_skill": self.user_profile.cooking_skill,
            "recipes_tried": len(self.user_profile.previous_recipes),
            "sessions_completed": len(self.user_profile.cooking_history)
        }
    
    def extract_recipe_name_from_response(self, response: str) -> str:
        """Extract recipe name from AI response."""
        try:
            # Look for recipe name patterns
            lines = response.split('\n')
            for line in lines:
                if "🍽️" in line and "**" in line:
                    # Extract text between ** markers
                    parts = line.split("**")
                    if len(parts) >= 3:
                        return parts[1]
            
            return "Recipe suggestion"
        except Exception as e:
            self.logger.error(f"Error extracting recipe name: {e}")
            return "Recipe suggestion"