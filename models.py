from dataclasses import dataclass, field
from typing import List, Dict, Optional, Any
from datetime import datetime, date
from enum import Enum
import json
import uuid

class DietaryRestriction(Enum):
    VEGETARIAN = "vegetarian"
    VEGAN = "vegan"
    GLUTEN_FREE = "gluten_free"
    DAIRY_FREE = "dairy_free"
    NUT_FREE = "nut_free"
    KETO = "keto"
    PALEO = "paleo"
    LOW_SODIUM = "low_sodium"
    DIABETIC = "diabetic"

class HealthCondition(Enum):
    DIABETES = "diabetes"
    HEART_DISEASE = "heart_disease"
    HIGH_BLOOD_PRESSURE = "high_blood_pressure"
    HIGH_CHOLESTEROL = "high_cholesterol"
    KIDNEY_DISEASE = "kidney_disease"
    CELIAC = "celiac"
    IBS = "ibs"
    OSTEOPOROSIS = "osteoporosis"

class CookingSkillLevel(Enum):
    BEGINNER = "beginner"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"

class MealType(Enum):
    BREAKFAST = "breakfast"
    LUNCH = "lunch"
    DINNER = "dinner"
    SNACK = "snack"

@dataclass
class FoodItem:
    """Represents a food item in inventory"""
    name: str
    quantity: str
    unit: str
    expiry_date: Optional[date] = None
    category: str = "other"
    priority: int = 0  # Higher number = use first
    nutritional_info: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'name': self.name,
            'quantity': self.quantity,
            'unit': self.unit,
            'expiry_date': self.expiry_date.isoformat() if self.expiry_date else None,
            'category': self.category,
            'priority': self.priority,
            'nutritional_info': self.nutritional_info
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'FoodItem':
        expiry_date = None
        if data.get('expiry_date'):
            expiry_date = date.fromisoformat(data['expiry_date'])
        
        return cls(
            name=data['name'],
            quantity=data['quantity'],
            unit=data['unit'],
            expiry_date=expiry_date,
            category=data.get('category', 'other'),
            priority=data.get('priority', 0),
            nutritional_info=data.get('nutritional_info', {})
        )

@dataclass
class CookingPreferences:
    """User cooking preferences and constraints"""
    skill_level: CookingSkillLevel = CookingSkillLevel.INTERMEDIATE
    available_time_minutes: int = 30
    preferred_cuisines: List[str] = field(default_factory=list)
    disliked_cuisines: List[str] = field(default_factory=list)
    kitchen_equipment: List[str] = field(default_factory=list)
    meal_prep_style: str = "daily"  # daily, batch, mixed
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'skill_level': self.skill_level.value,
            'available_time_minutes': self.available_time_minutes,
            'preferred_cuisines': self.preferred_cuisines,
            'disliked_cuisines': self.disliked_cuisines,
            'kitchen_equipment': self.kitchen_equipment,
            'meal_prep_style': self.meal_prep_style
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'CookingPreferences':
        return cls(
            skill_level=CookingSkillLevel(data.get('skill_level', 'intermediate')),
            available_time_minutes=data.get('available_time_minutes', 30),
            preferred_cuisines=data.get('preferred_cuisines', []),
            disliked_cuisines=data.get('disliked_cuisines', []),
            kitchen_equipment=data.get('kitchen_equipment', []),
            meal_prep_style=data.get('meal_prep_style', 'daily')
        )

@dataclass
class UserProfile:
    """Complete user profile for meal planning"""
    user_id: str
    food_preferences: List[str] = field(default_factory=list)
    food_dislikes: List[str] = field(default_factory=list)
    dietary_restrictions: List[DietaryRestriction] = field(default_factory=list)
    health_conditions: List[HealthCondition] = field(default_factory=list)
    cooking_preferences: CookingPreferences = field(default_factory=CookingPreferences)
    household_size: int = 1
    age_group: str = "adult"
    activity_level: str = "moderate"
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'user_id': self.user_id,
            'food_preferences': self.food_preferences,
            'food_dislikes': self.food_dislikes,
            'dietary_restrictions': [dr.value for dr in self.dietary_restrictions],
            'health_conditions': [hc.value for hc in self.health_conditions],
            'cooking_preferences': self.cooking_preferences.to_dict(),
            'household_size': self.household_size,
            'age_group': self.age_group,
            'activity_level': self.activity_level,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'UserProfile':
        return cls(
            user_id=data['user_id'],
            food_preferences=data.get('food_preferences', []),
            food_dislikes=data.get('food_dislikes', []),
            dietary_restrictions=[
                DietaryRestriction(dr) for dr in data.get('dietary_restrictions', [])
            ],
            health_conditions=[
                HealthCondition(hc) for hc in data.get('health_conditions', [])
            ],
            cooking_preferences=CookingPreferences.from_dict(
                data.get('cooking_preferences', {})
            ),
            household_size=data.get('household_size', 1),
            age_group=data.get('age_group', 'adult'),
            activity_level=data.get('activity_level', 'moderate'),
            created_at=datetime.fromisoformat(data.get('created_at', datetime.utcnow().isoformat())),
            updated_at=datetime.fromisoformat(data.get('updated_at', datetime.utcnow().isoformat()))
        )

@dataclass
class Recipe:
    """Recipe suggestion with metadata"""
    name: str
    ingredients: List[str]
    instructions: List[str]
    cooking_time_minutes: int
    prep_time_minutes: int
    servings: int
    difficulty_level: CookingSkillLevel
    nutrition_info: Dict[str, Any] = field(default_factory=dict)
    tags: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'name': self.name,
            'ingredients': self.ingredients,
            'instructions': self.instructions,
            'cooking_time_minutes': self.cooking_time_minutes,
            'prep_time_minutes': self.prep_time_minutes,
            'servings': self.servings,
            'difficulty_level': self.difficulty_level.value,
            'nutrition_info': self.nutrition_info,
            'tags': self.tags
        }

@dataclass
class Meal:
    """Single meal in a meal plan"""
    meal_type: MealType
    recipe: Recipe
    scheduled_date: date
    ingredients_used: List[FoodItem] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'meal_type': self.meal_type.value,
            'recipe': self.recipe.to_dict(),
            'scheduled_date': self.scheduled_date.isoformat(),
            'ingredients_used': [item.to_dict() for item in self.ingredients_used]
        }

@dataclass
class MealPlan:
    """Complete meal plan for multiple days"""
    plan_id: str
    user_id: str
    start_date: date
    end_date: date
    meals: List[Meal]
    shopping_list: List[FoodItem] = field(default_factory=list)
    waste_reduction_tips: List[str] = field(default_factory=list)
    nutritional_summary: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.utcnow)
    
    def __post_init__(self):
        if not self.plan_id:
            self.plan_id = str(uuid.uuid4())
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'plan_id': self.plan_id,
            'user_id': self.user_id,
            'start_date': self.start_date.isoformat(),
            'end_date': self.end_date.isoformat(),
            'meals': [meal.to_dict() for meal in self.meals],
            'shopping_list': [item.to_dict() for item in self.shopping_list],
            'waste_reduction_tips': self.waste_reduction_tips,
            'nutritional_summary': self.nutritional_summary,
            'created_at': self.created_at.isoformat()
        }

@dataclass
class AgentResponse:
    """Standardized response from agents"""
    agent_name: str
    success: bool
    data: Dict[str, Any] = field(default_factory=dict)
    errors: List[str] = field(default_factory=list)
    confidence_score: float = 0.0
    processing_time: float = 0.0
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'agent_name': self.agent_name,
            'success': self.success,
            'data': self.data,
            'errors': self.errors,
            'confidence_score': self.confidence_score,
            'processing_time': self.processing_time
        }

@dataclass
class UserInventory:
    """User's current food inventory"""
    user_id: str
    items: List[FoodItem] = field(default_factory=list)
    last_updated: datetime = field(default_factory=datetime.utcnow)
    
    def get_expiring_soon(self, days: int = 3) -> List[FoodItem]:
        """Get items expiring within specified days"""
        from datetime import timedelta
        cutoff_date = date.today() + timedelta(days=days)
        return [
            item for item in self.items 
            if item.expiry_date and item.expiry_date <= cutoff_date
        ]
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'user_id': self.user_id,
            'items': [item.to_dict() for item in self.items],
            'last_updated': self.last_updated.isoformat()
        }
    