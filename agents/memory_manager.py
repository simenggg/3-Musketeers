import json
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime

from models import UserProfile, UserInventory, FoodItem, AgentResponse
from database import db
from bedrock_client import bedrock_client

logger = logging.getLogger(__name__)

class MemoryManagerAgent:
    """
    Agent responsible for managing user memory and profile information
    """
    
    def __init__(self):
        self.agent_name = "MemoryManager"
        self.system_prompt = self._get_system_prompt()
    
    def _get_system_prompt(self) -> str:
        return """You are the Memory Manager Agent for "Good Food to You". Your role is to maintain and update the user's persistent knowledge base for personalized meal planning.

Your responsibilities:
1. Extract and validate user information updates
2. Maintain consistent user profiles
3. Track food inventory changes
4. Identify conflicts or important changes
5. Ensure data integrity and safety

Always respond with valid JSON in this exact format:
{
  "updates_detected": boolean,
  "changes_summary": "Brief description of what changed",
  "updated_profile": {
    "food_preferences": [],
    "food_dislikes": [],
    "dietary_restrictions": [],
    "health_conditions": [],
    "cooking_preferences": {},
    "household_size": number,
    "age_group": "string",
    "activity_level": "string"
  },
  "inventory_updates": [
    {
      "action": "add|update|remove",
      "item": {
        "name": "string",
        "quantity": "string",
        "unit": "string",
        "expiry_date": "YYYY-MM-DD or null",
        "category": "string",
        "priority": number
      }
    }
  ],
  "alerts": [],
  "confidence_score": 0.0-1.0
}

Be extremely careful with health-related information and dietary restrictions."""

    async def process_user_input(
        self, 
        user_id: str, 
        user_input: str, 
        current_profile: Optional[UserProfile] = None,
        current_inventory: Optional[UserInventory] = None
    ) -> AgentResponse:
        """
        Process user input to extract profile and inventory updates
        """
        try:
            # Get current profile if not provided
            if not current_profile:
                current_profile = await db.get_user_profile(user_id)
            
            # Get current inventory if not provided
            if not current_inventory:
                current_inventory = await db.get_user_inventory(user_id)
            
            # Build context for the agent
            context = self._build_context(user_input, current_profile, current_inventory)
            
            # Invoke the model
            response = await bedrock_client.invoke_with_retry(
                prompt=context,
                agent_name=self.agent_name,
                system_prompt=self.system_prompt,
                temperature=0.1
            )
            
            if not response.success:
                return response
            
            # Process the agent's response
            processed_response = await self._process_agent_response(
                user_id, response.data, current_profile, current_inventory
            )
            
            return processed_response
            
        except Exception as e:
            logger.error(f"Error in MemoryManager process_user_input: {str(e)}")
            return AgentResponse(
                agent_name=self.agent_name,
                success=False,
                errors=[f"Processing error: {str(e)}"]
            )
    
    def _build_context(
        self, 
        user_input: str, 
        profile: Optional[UserProfile], 
        inventory: Optional[UserInventory]
    ) -> str:
        """
        Build context prompt for the memory manager
        """
        context_parts = []
        
        # Current profile information
        if profile:
            context_parts.append("## Current User Profile:")
            context_parts.append(f"Food Preferences: {', '.join(profile.food_preferences)}")
            context_parts.append(f"Food Dislikes: {', '.join(profile.food_dislikes)}")
            context_parts.append(f"Dietary Restrictions: {[dr.value for dr in profile.dietary_restrictions]}")
            context_parts.append(f"Health Conditions: {[hc.value for hc in profile.health_conditions]}")
            context_parts.append(f"Household Size: {profile.household_size}")
            context_parts.append(f"Age Group: {profile.age_group}")
            context_parts.append(f"Activity Level: {profile.activity_level}")
            context_parts.append(f"Cooking Preferences: {profile.cooking_preferences.to_dict()}")
        else:
            context_parts.append("## Current User Profile: No existing profile")
        
        # Current inventory information
        if inventory and inventory.items:
            context_parts.append("\n## Current Inventory:")
            for item in inventory.items[:20]:  # Limit to avoid token limits
                expiry_str = item.expiry_date.strftime("%Y-%m-%d") if item.expiry_date else "No expiry"
                context_parts.append(f"- {item.name}: {item.quantity} {item.unit} (expires: {expiry_str})")
        else:
            context_parts.append("\n## Current Inventory: Empty")
        
        context_parts.append(f"\n## New User Input:\n{user_input}")
        
        context_parts.append("\n## Instructions:")
        context_parts.append("Analyze the user input and extract any updates to their profile or inventory.")
        context_parts.append("Be careful to distinguish between adding new items and updating existing ones.")
        context_parts.append("For food items, try to determine reasonable expiry dates if not specified.")
        context_parts.append("Flag any potential conflicts with dietary restrictions or health conditions.")
        
        return "\n".join(context_parts)
    
    async def _process_agent_response(
        self,
        user_id: str,
        agent_data: Dict[str, Any],
        current_profile: Optional[UserProfile],
        current_inventory: Optional[UserInventory]
    ) -> AgentResponse:
        """
        Process the agent's response and update database
        """
        try:
            # Extract updates from agent response
            if 'raw_response' in agent_data:
                # Try to parse JSON from raw response
                parsed_data = bedrock_client.extract_json_from_response(agent_data['raw_response'])
                if parsed_data:
                    agent_data = parsed_data
                else:
                    return AgentResponse(
                        agent_name=self.agent_name,
                        success=False,
                        errors=["Could not parse agent response as JSON"]
                    )
            
            updates_made = []
            
            # Update profile if changes detected
            if agent_data.get('updates_detected', False):
                profile_updates = agent_data.get('updated_profile', {})
                
                if current_profile:
                    # Update existing profile
                    await self._update_profile_fields(current_profile, profile_updates)
                    if await db.save_user_profile(current_profile):
                        updates_made.append("profile_updated")
                else:
                    # Create new profile
                    new_profile = self._create_profile_from_updates(user_id, profile_updates)
                    if await db.save_user_profile(new_profile):
                        updates_made.append("profile_created")
                        current_profile = new_profile
            
            # Update inventory if changes detected
            inventory_updates = agent_data.get('inventory_updates', [])
            if inventory_updates:
                current_inventory = await self._process_inventory_updates(
                    user_id, inventory_updates, current_inventory
                )
                if current_inventory:
                    updates_made.append("inventory_updated")
            
            return AgentResponse(
                agent_name=self.agent_name,
                success=True,
                data={
                    'updates_made': updates_made,
                    'changes_summary': agent_data.get('changes_summary', ''),
                    'alerts': agent_data.get('alerts', []),
                    'updated_profile': current_profile.to_dict() if current_profile else None,
                    'updated_inventory': current_inventory.to_dict() if current_inventory else None
                },
                confidence_score=agent_data.get('confidence_score', 0.8)
            )
            
        except Exception as e:
            logger.error(f"Error processing agent response: {str(e)}")
            return AgentResponse(
                agent_name=self.agent_name,
                success=False,
                errors=[f"Response processing error: {str(e)}"]
            )
    
    def _update_profile_fields(self, profile: UserProfile, updates: Dict[str, Any]):
        """
        Update profile fields with new data
        """
        if 'food_preferences' in updates:
            profile.food_preferences = updates['food_preferences']
        
        if 'food_dislikes' in updates:
            profile.food_dislikes = updates['food_dislikes']
        
        if 'dietary_restrictions' in updates:
            from models import DietaryRestriction
            profile.dietary_restrictions = [
                DietaryRestriction(dr) for dr in updates['dietary_restrictions']
                if dr in [item.value for item in DietaryRestriction]
            ]
        
        if 'health_conditions' in updates:
            from models import HealthCondition
            profile.health_conditions = [
                HealthCondition(hc) for hc in updates['health_conditions']
                if hc in [item.value for item in HealthCondition]
            ]
        
        if 'household_size' in updates:
            profile.household_size = updates['household_size']
        
        if 'age_group' in updates:
            profile.age_group = updates['age_group']
        
        if 'activity_level' in updates:
            profile.activity_level = updates['activity_level']
        
        if 'cooking_preferences' in updates:
            from models import CookingPreferences
            profile.cooking_preferences = CookingPreferences.from_dict(updates['cooking_preferences'])
        
        profile.updated_at = datetime.utcnow()
    
    def _create_profile_from_updates(self, user_id: str, updates: Dict[str, Any]) -> UserProfile:
        """
        Create new profile from update data
        """
        from models import DietaryRestriction, HealthCondition, CookingPreferences
        
        profile = UserProfile(user_id=user_id)
        
        profile.food_preferences = updates.get('food_preferences', [])
        profile.food_dislikes = updates.get('food_dislikes', [])
        
        # Handle dietary restrictions
        dietary_restrictions = updates.get('dietary_restrictions', [])
        profile.dietary_restrictions = [
            DietaryRestriction(dr) for dr in dietary_restrictions
            if dr in [item.value for item in DietaryRestriction]
        ]
        
        # Handle health conditions
        health_conditions = updates.get('health_conditions', [])
        profile.health_conditions = [
            HealthCondition(hc) for hc in health_conditions
            if hc in [item.value for item in HealthCondition]
        ]
        
        profile.household_size = updates.get('household_size', 1)
        profile.age_group = updates.get('age_group', 'adult')
        profile.activity_level = updates.get('activity_level', 'moderate')
        
        # Handle cooking preferences
        cooking_prefs = updates.get('cooking_preferences', {})
        profile.cooking_preferences = CookingPreferences.from_dict(cooking_prefs)
        
        return profile
    
    async def _process_inventory_updates(
        self, 
        user_id: str, 
        updates: List[Dict[str, Any]], 
        current_inventory: Optional[UserInventory]
    ) -> Optional[UserInventory]:
        """
        Process inventory updates
        """
        try:
            if not current_inventory:
                current_inventory = UserInventory(user_id=user_id, items=[])
            
            for update in updates:
                action = update.get('action', '')
                item_data = update.get('item', {})
                
                if action == 'add' or action == 'update':
                    # Parse expiry date
                    expiry_date = None
                    if item_data.get('expiry_date'):
                        try:
                            from datetime import datetime
                            expiry_date = datetime.strptime(
                                item_data['expiry_date'], '%Y-%m-%d'
                            ).date()
                        except ValueError:
                            logger.warning(f"Invalid expiry date format: {item_data['expiry_date']}")
                    
                    food_item = FoodItem(
                        name=item_data['name'],
                        quantity=item_data.get('quantity', '1'),
                        unit=item_data.get('unit', 'piece'),
                        expiry_date=expiry_date,
                        category=item_data.get('category', 'other'),
                        priority=item_data.get('priority', 0)
                    )
                    
                    # Add or update item
                    await db.add_inventory_item(user_id, food_item)
                
                elif action == 'remove':
                    item_name = item_data.get('name', '')
                    if item_name:
                        await db.remove_inventory_item(user_id, item_name)
            
            # Get updated inventory
            return await db.get_user_inventory(user_id)
            
        except Exception as e:
            logger.error(f"Error processing inventory updates: {str(e)}")
            return current_inventory
    
    async def get_user_context(self, user_id: str) -> Dict[str, Any]:
        """
        Get complete user context for other agents
        """
        try:
            profile = await db.get_user_profile(user_id)
            inventory = await db.get_user_inventory(user_id)
            
            context = {
                'user_id': user_id,
                'profile': profile.to_dict() if profile else None,
                'inventory': inventory.to_dict() if inventory else None,
                'expiring_items': []
            }
            
            if inventory:
                expiring_items = inventory.get_expiring_soon(days=3)
                context['expiring_items'] = [item.to_dict() for item in expiring_items]
            
            return context
            
        except Exception as e:
            logger.error(f"Error getting user context: {str(e)}")
            return {'user_id': user_id, 'error': str(e)}

# Global memory manager instance
memory_manager = MemoryManagerAgent()