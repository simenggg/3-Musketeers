"""Data models for recipes and meal planning."""

from datetime import datetime
from typing import List, Dict, Any, Optional
from dataclasses import dataclass


@dataclass
class Recipe:
    """Represents a recipe with ingredients and instructions."""
    
    name: str
    ingredients: List[str]
    instructions: List[str]
    prep_time: int  # minutes
    cook_time: int  # minutes
    servings: int
    difficulty: str  # easy, medium, hard
    cuisine: str
    meal_type: str  # breakfast, lunch, dinner, snack
    priority_ingredients: List[str] = None  # expiring ingredients
    
    def __post_init__(self):
        if self.priority_ingredients is None:
            self.priority_ingredients = []
    
    @property
    def total_time(self) -> int:
        """Total cooking time in minutes."""
        return self.prep_time + self.cook_time
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            'name': self.name,
            'ingredients': self.ingredients,
            'instructions': self.instructions,
            'prep_time': self.prep_time,
            'cook_time': self.cook_time,
            'servings': self.servings,
            'difficulty': self.difficulty,
            'cuisine': self.cuisine,
            'meal_type': self.meal_type,
            'priority_ingredients': self.priority_ingredients
        }


@dataclass
class UserProfile:
    """User preferences and cooking history."""
    
    dietary_restrictions: str = ""
    dislikes: List[str] = None
    favorite_cuisines: List[str] = None
    cooking_skill: str = "beginner"
    previous_recipes: List[Dict] = None
    cooking_history: List[Dict] = None
    meal_preferences: Dict[str, List[str]] = None
    
    def __post_init__(self):
        if self.dislikes is None:
            self.dislikes = []
        if self.favorite_cuisines is None:
            self.favorite_cuisines = []
        if self.previous_recipes is None:
            self.previous_recipes = []
        if self.cooking_history is None:
            self.cooking_history = []
        if self.meal_preferences is None:
            self.meal_preferences = {
                "breakfast": [],
                "lunch": [],
                "dinner": [],
                "snacks": []
            }