import json
import logging
from typing import Dict, Any, List, Optional

from models import AgentResponse, UserProfile
from bedrock_client import bedrock_client

logger = logging.getLogger(__name__)

class NutritionResearchAgent:
    """
    Agent responsible for nutritional guidance and meal plan validation
    """
    
    def __init__(self):
        self.agent_name = "NutritionResearch"
        self.system_prompt = self._get_system_prompt()
    
    def _get_system_prompt(self) -> str:
        return """You are the Nutrition Research Agent for "Good Food to You". You provide evidence-based nutritional guidance and validate meal plans against dietary needs and health conditions.

Your responsibilities:
1. Assess nutritional completeness of meal plans
2. Validate against health conditions and dietary restrictions
3. Provide evidence-based recommendations
4. Flag potential nutrient deficiencies or excesses
5. Suggest modifications for optimal health

Always respond with valid JSON in this exact format:
{
  "nutritional_assessment": {
    "overall_score": 0-100,
    "strengths": ["list of nutritional strengths"],
    "concerns": ["list of nutritional concerns"],
    "missing_nutrients": ["list of potentially missing nutrients"]
  },
  "health_specific_recommendations": [
    {
      "condition": "health condition name",
      "recommendations": ["specific dietary advice"],
      "foods_to_emphasize": ["foods to include more"],
      "foods_to_limit": ["foods to limit or avoid"]
    }
  ],
  "suggested_modifications": [
    {
      "meal": "meal name or general",
      "modification": "specific suggestion",
      "reason": "nutritional rationale"
    }
  ],
  "daily_nutrition_targets": {
    "calories": "target range",
    "protein_g": "target range",
    "fiber_g": "target range",
    "key_micronutrients": {}
  },
  "confidence_level": 0.0-1.0
}

Base recommendations on current dietary guidelines and peer-reviewed research. Prioritize safety for users with health conditions."""

    async def validate_meal_plan(
        self, 
        meal_plan_data: Dict[str, Any], 
        user_profile: UserProfile,
        user_input: Optional[str] = None
    ) -> AgentResponse:
        """
        Validate a meal plan against nutritional requirements and health conditions
        """
        try:
            # Build validation context
            context = self._build_validation_context(meal_plan_data, user_profile, user_input)
            
            # Invoke the model
            response = await bedrock_client.invoke_with_retry(
                prompt=context,
                agent_name=self.agent_name,
                system_prompt=self.system_prompt,
                temperature=0.1
            )
            
            if not response.success:
                return response
            
            # Process the response
            return await self._process_validation_response(response.data, user_profile)
            
        except Exception as e:
            logger.error(f"Error in NutritionResearch validate_meal_plan: {str(e)}")
            return AgentResponse(
                agent_name=self.agent_name,
                success=False,
                errors=[f"Validation error: {str(e)}"]
            )
    
    async def research_health_condition_requirements(
        self, 
        health_conditions: List[str],
        user_context: Dict[str, Any]
    ) -> AgentResponse:
        """
        Research specific nutritional requirements for health conditions
        """
        try:
            context = self._build_health_research_context(health_conditions, user_context)
            
            response = await bedrock_client.invoke_with_retry(
                prompt=context,
                agent_name=self.agent_name,
                system_prompt=self.system_prompt,
                temperature=0.1
            )
            
            if not response.success:
                return response
            
            return await self._process_research_response(response.data)
            
        except Exception as e:
            logger.error(f"Error in health condition research: {str(e)}")
            return AgentResponse(
                agent_name=self.agent_name,
                success=False,
                errors=[f"Research error: {str(e)}"]
            )
    
    def _build_validation_context(
        self, 
        meal_plan_data: Dict[str, Any], 
        user_profile: UserProfile,
        user_input: Optional[str] = None
    ) -> str:
        """
        Build context for meal plan validation
        """
        context_parts = []
        
        # User profile information
        context_parts.append("## User Profile:")
        context_parts.append(f"Age Group: {user_profile.age_group}")
        context_parts.append(f"Activity Level: {user_profile.activity_level}")
        context_parts.append(f"Household Size: {user_profile.household_size}")
        
        # Dietary restrictions and health conditions
        if user_profile.dietary_restrictions:
            restrictions = [dr.value for dr in user_profile.dietary_restrictions]
            context_parts.append(f"Dietary Restrictions: {', '.join(restrictions)}")
        
        if user_profile.health_conditions:
            conditions = [hc.value for hc in user_profile.health_conditions]
            context_parts.append(f"Health Conditions: {', '.join(conditions)}")
        
        # Cooking preferences
        cooking_prefs = user_profile.cooking_preferences
        context_parts.append(f"Available Cooking Time: {cooking_prefs.available_time_minutes} minutes")
        context_parts.append(f"Skill Level: {cooking_prefs.skill_level.value}")
        
        # Meal plan data
        context_parts.append("\n## Proposed Meal Plan:")
        if 'meals' in meal_plan_data:
            for meal in meal_plan_data['meals'][:10]:  # Limit for token management
                meal_info = meal.get('recipe', {})
                context_parts.append(f"- {meal.get('meal_type', 'Unknown')}: {meal_info.get('name', 'Unknown recipe')}")
                if 'ingredients' in meal_info:
                    ingredients = meal_info['ingredients'][:5]  # Limit ingredients
                    context_parts.append(f"  Ingredients: {', '.join(ingredients)}")
                if 'nutrition_info' in meal_info:
                    nutrition = meal_info['nutrition_info']
                    if nutrition:
                        context_parts.append(f"  Nutrition: {nutrition}")
        
        # Additional context from user input
        if user_input:
            context_parts.append(f"\n## Additional User Input:\n{user_input}")
        
        # Validation instructions
        context_parts.append("\n## Validation Instructions:")
        context_parts.append("1. Assess overall nutritional balance across all meals")
        context_parts.append("2. Check compliance with dietary restrictions and health conditions")
        context_parts.append("3. Identify potential nutrient gaps or excesses")
        context_parts.append("4. Consider age group and activity level requirements")
        context_parts.append("5. Suggest specific improvements with rationale")
        
        return "\n".join(context_parts)
    
    def _build_health_research_context(
        self, 
        health_conditions: List[str], 
        user_context: Dict[str, Any]
    ) -> str:
        """
        Build context for health condition research
        """
        context_parts = []
        
        context_parts.append("## Health Conditions to Research:")
        for condition in health_conditions:
            context_parts.append(f"- {condition}")
        
        context_parts.append("\n## User Context:")
        if 'age_group' in user_context:
            context_parts.append(f"Age Group: {user_context['age_group']}")
        if 'activity_level' in user_context:
            context_parts.append(f"Activity Level: {user_context['activity_level']}")
        if 'dietary_restrictions' in user_context:
            context_parts.append(f"Existing Dietary Restrictions: {user_context['dietary_restrictions']}")
        
        context_parts.append("\n## Research Instructions:")
        context_parts.append("1. Provide evidence-based dietary recommendations for each health condition")
        context_parts.append("2. Identify key nutrients of concern (deficiency or excess)")
        context_parts.append("3. Suggest specific foods to emphasize and limit")
        context_parts.append("4. Consider interactions between multiple conditions")
        context_parts.append("5. Provide practical, actionable advice")
        context_parts.append("6. Note any medication-food interactions if relevant")
        
        return "\n".join(context_parts)
    
    async def _process_validation_response(
        self, 
        agent_data: Dict[str, Any], 
        user_profile: UserProfile
    ) -> AgentResponse:
        """
        Process validation response from the agent
        """
        try:
            # Extract JSON if needed
            if 'raw_response' in agent_data:
                parsed_data = bedrock_client.extract_json_from_response(agent_data['raw_response'])
                if parsed_data:
                    agent_data = parsed_data
                else:
                    return AgentResponse(
                        agent_name=self.agent_name,
                        success=False,
                        errors=["Could not parse nutrition validation response as JSON"]
                    )
            
            # Validate required fields
            required_fields = ['nutritional_assessment', 'health_specific_recommendations', 'suggested_modifications']
            if not bedrock_client.validate_response_format(agent_data, required_fields):
                return AgentResponse(
                    agent_name=self.agent_name,
                    success=False,
                    errors=["Invalid response format from nutrition agent"]
                )
            
            # Process and enhance the data
            processed_data = {
                'validation_results': agent_data,
                'user_profile_considered': {
                    'dietary_restrictions': [dr.value for dr in user_profile.dietary_restrictions],
                    'health_conditions': [hc.value for hc in user_profile.health_conditions],
                    'age_group': user_profile.age_group,
                    'activity_level': user_profile.activity_level
                },
                'recommendations_priority': self._prioritize_recommendations(agent_data),
                'safety_alerts': self._identify_safety_alerts(agent_data, user_profile)
            }
            
            return AgentResponse(
                agent_name=self.agent_name,
                success=True,
                data=processed_data,
                confidence_score=agent_data.get('confidence_level', 0.8)
            )
            
        except Exception as e:
            logger.error(f"Error processing validation response: {str(e)}")
            return AgentResponse(
                agent_name=self.agent_name,
                success=False,
                errors=[f"Response processing error: {str(e)}"]
            )
    
    async def _process_research_response(self, agent_data: Dict[str, Any]) -> AgentResponse:
        """
        Process research response from the agent
        """
        try:
            # Extract JSON if needed
            if 'raw_response' in agent_data:
                parsed_data = bedrock_client.extract_json_from_response(agent_data['raw_response'])
                if parsed_data:
                    agent_data = parsed_data
                else:
                    return AgentResponse(
                        agent_name=self.agent_name,
                        success=False,
                        errors=["Could not parse research response as JSON"]
                    )
            
            return AgentResponse(
                agent_name=self.agent_name,
                success=True,
                data=agent_data,
                confidence_score=agent_data.get('confidence_level', 0.8)
            )
            
        except Exception as e:
            logger.error(f"Error processing research response: {str(e)}")
            return AgentResponse(
                agent_name=self.agent_name,
                success=False,
                errors=[f"Research processing error: {str(e)}"]
            )
    
    def _prioritize_recommendations(self, validation_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Prioritize recommendations based on health impact
        """
        recommendations = []
        
        # Health-specific recommendations get highest priority
        health_recs = validation_data.get('health_specific_recommendations', [])
        for rec in health_recs:
            recommendations.append({
                'priority': 'high',
                'type': 'health_specific',
                'content': rec,
                'reason': f"Important for managing {rec.get('condition', 'health condition')}"
            })
        
        # Nutritional concerns get medium-high priority
        assessment = validation_data.get('nutritional_assessment', {})
        concerns = assessment.get('concerns', [])
        for concern in concerns:
            recommendations.append({
                'priority': 'medium-high',
                'type': 'nutritional_concern',
                'content': concern,
                'reason': 'Addresses nutritional deficiency or imbalance'
            })
        
        # General modifications get medium priority
        modifications = validation_data.get('suggested_modifications', [])
        for mod in modifications:
            recommendations.append({
                'priority': 'medium',
                'type': 'meal_modification',
                'content': mod,
                'reason': mod.get('reason', 'General improvement')
            })
        
        return recommendations
    
    def _identify_safety_alerts(
        self, 
        validation_data: Dict[str, Any], 
        user_profile: UserProfile
    ) -> List[Dict[str, Any]]:
        """
        Identify potential safety concerns
        """
        alerts = []
        
        # Check for dietary restriction violations
        assessment = validation_data.get('nutritional_assessment', {})
        concerns = assessment.get('concerns', [])
        
        dietary_keywords = {
            'gluten': ['gluten_free'],
            'dairy': ['dairy_free'],
            'meat': ['vegetarian', 'vegan'],
            'animal': ['vegan'],
            'nuts': ['nut_free']
        }
        
        user_restrictions = [dr.value for dr in user_profile.dietary_restrictions]
        
        for concern in concerns:
            concern_lower = concern.lower()
            for keyword, restrictions in dietary_keywords.items():
                if keyword in concern_lower:
                    for restriction in restrictions:
                        if restriction in user_restrictions:
                            alerts.append({
                                'severity': 'high',
                                'type': 'dietary_restriction_violation',
                                'message': f"Potential {restriction} violation detected: {concern}",
                                'action': 'Review meal plan ingredients carefully'
                            })
        
        # Check for health condition conflicts
        health_conditions = [hc.value for hc in user_profile.health_conditions]
        health_recs = validation_data.get('health_specific_recommendations', [])
        
        for rec in health_recs:
            foods_to_limit = rec.get('foods_to_limit', [])
            if foods_to_limit:
                alerts.append({
                    'severity': 'medium',
                    'type': 'health_condition_concern',
                    'message': f"For {rec.get('condition', 'your condition')}, limit: {', '.join(foods_to_limit)}",
                    'action': 'Consider modifying meal plan to reduce these foods'
                })
        
        return alerts
    
    async def get_nutrition_guidelines(
        self, 
        age_group: str, 
        activity_level: str, 
        health_conditions: List[str] = None
    ) -> AgentResponse:
        """
        Get general nutrition guidelines for user demographics
        """
        try:
            context_parts = []
            context_parts.append(f"## User Demographics:")
            context_parts.append(f"Age Group: {age_group}")
            context_parts.append(f"Activity Level: {activity_level}")
            
            if health_conditions:
                context_parts.append(f"Health Conditions: {', '.join(health_conditions)}")
            
            context_parts.append("\n## Request:")
            context_parts.append("Provide general nutrition guidelines and daily targets for this user profile.")
            context_parts.append("Include macronutrient distributions, key micronutrients, and general dietary advice.")
            
            context = "\n".join(context_parts)
            
            response = await bedrock_client.invoke_with_retry(
                prompt=context,
                agent_name=self.agent_name,
                system_prompt=self.system_prompt,
                temperature=0.1
            )
            
            return response
            
        except Exception as e:
            logger.error(f"Error getting nutrition guidelines: {str(e)}")
            return AgentResponse(
                agent_name=self.agent_name,
                success=False,
                errors=[f"Guidelines error: {str(e)}"]
            )
    
    def calculate_meal_nutrition_score(self, meal_data: Dict[str, Any]) -> float:
        """
        Calculate a simple nutrition score for a meal (0-100)
        """
        score = 50  # Base score
        
        # Check for variety in ingredients
        ingredients = meal_data.get('ingredients', [])
        if len(ingredients) >= 5:
            score += 10
        elif len(ingredients) >= 3:
            score += 5
        
        # Check for presence of key food groups
        ingredient_text = ' '.join(ingredients).lower()
        
        food_groups = {
            'protein': ['chicken', 'fish', 'beef', 'pork', 'beans', 'tofu', 'eggs', 'quinoa'],
            'vegetables': ['broccoli', 'spinach', 'carrots', 'peppers', 'tomatoes', 'onions'],
            'whole_grains': ['brown rice', 'quinoa', 'oats', 'whole wheat', 'barley'],
            'healthy_fats': ['olive oil', 'avocado', 'nuts', 'seeds', 'salmon']
        }
        
        groups_present = 0
        for group, foods in food_groups.items():
            if any(food in ingredient_text for food in foods):
                groups_present += 1
                score += 8
        
        # Bonus for having multiple food groups
        if groups_present >= 3:
            score += 10
        
        # Check cooking method (if available)
        instructions = meal_data.get('instructions', [])
        instruction_text = ' '.join(instructions).lower()
        
        healthy_methods = ['steam', 'grill', 'bake', 'roast', 'sauté']
        less_healthy_methods = ['deep fry', 'fry']
        
        if any(method in instruction_text for method in healthy_methods):
            score += 5
        elif any(method in instruction_text for method in less_healthy_methods):
            score -= 10
        
        return min(100, max(0, score))

# Global nutrition research agent instance
nutrition_researcher = NutritionResearchAgent()