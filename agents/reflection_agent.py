import json
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta

from models import AgentResponse, UserProfile
from bedrock_client import bedrock_client
from database import db

logger = logging.getLogger(__name__)

class ReflectionAgent:
    """
    Agent responsible for learning from user feedback and improving recommendations
    """
    
    def __init__(self):
        self.agent_name = "Reflection"
        self.system_prompt = self._get_system_prompt()
    
    def _get_system_prompt(self) -> str:
        return """You are the Reflection Agent for "Good Food to You". Your role is to learn from user interactions and feedback to continuously improve meal planning recommendations.

Your responsibilities:
1. Analyze user feedback on meal plans and recipes
2. Identify patterns in user preferences and behaviors
3. Learn from successful and unsuccessful recommendations
4. Suggest system improvements and personalization adjustments
5. Track user satisfaction and engagement metrics

Always respond with valid JSON in this exact format:
{
  "analysis": {
    "feedback_sentiment": "positive|negative|mixed|neutral",
    "key_insights": ["list of insights learned"],
    "preference_updates": {
      "new_likes": ["items user seems to enjoy"],
      "new_dislikes": ["items user seems to avoid"],
      "cooking_style_preferences": ["observed preferences"],
      "timing_preferences": ["when user prefers to cook"]
    },
    "success_factors": ["what made recommendations work well"],
    "failure_points": ["what didn't work and why"]
  },
  "recommendations": {
    "profile_adjustments": ["suggested changes to user profile"],
    "algorithm_improvements": ["ways to improve meal planning"],
    "personalization_updates": ["specific customizations for this user"]
  },
  "learning_summary": {
    "confidence_in_analysis": 0.0-1.0,
    "data_quality_score": 0.0-1.0,
    "actionable_insights_count": number
  },
  "next_steps": ["specific actions to take based on this learning"]
}

Focus on extracting actionable insights that will improve future meal planning for this specific user."""

    async def analyze_user_feedback(
        self,
        user_id: str,
        feedback_data: Dict[str, Any],
        meal_plan_history: List[Dict[str, Any]] = None,
        user_profile: UserProfile = None
    ) -> AgentResponse:
        """
        Analyze user feedback to extract learning insights
        """
        try:
            # Get user context if not provided
            if not user_profile:
                user_profile = await db.get_user_profile(user_id)
            
            if not meal_plan_history:
                meal_plan_history = await db.get_user_meal_history(user_id, limit=5)
            
            # Build analysis context
            context = self._build_feedback_context(
                feedback_data, meal_plan_history, user_profile
            )
            
            # Invoke the model
            response = await bedrock_client.invoke_with_retry(
                prompt=context,
                agent_name=self.agent_name,
                system_prompt=self.system_prompt,
                temperature=0.2
            )
            
            if not response.success:
                return response
            
            # Process and apply insights
            return await self._process_learning_insights(
                user_id, response.data, user_profile
            )
            
        except Exception as e:
            logger.error(f"Error in Reflection analyze_user_feedback: {str(e)}")
            return AgentResponse(
                agent_name=self.agent_name,
                success=False,
                errors=[f"Feedback analysis error: {str(e)}"]
            )
    
    def _build_feedback_context(
        self,
        feedback_data: Dict[str, Any],
        meal_plan_history: List[Dict[str, Any]],
        user_profile: Optional[UserProfile]
    ) -> str:
        """
        Build context for feedback analysis
        """
        context_parts = []
        
        # Current feedback
        context_parts.append("## Current User Feedback:")
        context_parts.append(json.dumps(feedback_data, indent=2))
        
        # User profile context
        if user_profile:
            context_parts.append("\n## User Profile:")
            context_parts.append(f"Food Preferences: {', '.join(user_profile.food_preferences)}")
            context_parts.append(f"Food Dislikes: {', '.join(user_profile.food_dislikes)}")
            context_parts.append(f"Dietary Restrictions: {[dr.value for dr in user_profile.dietary_restrictions]}")
            context_parts.append(f"Cooking Skill: {user_profile.cooking_preferences.skill_level.value}")
            context_parts.append(f"Available Time: {user_profile.cooking_preferences.available_time_minutes} min")
        
        # Historical meal plans
        if meal_plan_history:
            context_parts.append("\n## Recent Meal Plan History:")
            for i, plan in enumerate(meal_plan_history[:3], 1):
                context_parts.append(f"### Plan {i} (Created: {plan.get('created_at', 'Unknown')}):")
                
                # Extract key information about past plans
                meals = plan.get('meals', [])[:5]  # Limit for token management
                for meal in meals:
                    recipe = meal.get('recipe', {})
                    context_parts.append(f"- {meal.get('meal_type', 'unknown')}: {recipe.get('name', 'Unknown')}")
                
                # Include any previous feedback
                if 'user_feedback' in plan:
                    context_parts.append(f"Previous feedback: {plan['user_feedback']}")
        
        # Analysis instructions
        context_parts.append("\n## Analysis Instructions:")
        context_parts.append("1. Identify specific likes and dislikes from the feedback")
        context_parts.append("2. Look for patterns in cooking preferences and time constraints")
        context_parts.append("3. Determine what aspects of meal planning are working well")
        context_parts.append("4. Identify areas where recommendations can be improved")
        context_parts.append("5. Consider how this feedback aligns with the user's stated preferences")
        context_parts.append("6. Extract actionable insights for future meal planning")
        
        return "\n".join(context_parts)
    
    async def _process_learning_insights(
        self,
        user_id: str,
        agent_data: Dict[str, Any],
        user_profile: Optional[UserProfile]
    ) -> AgentResponse:
        """
        Process learning insights and apply profile updates
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
                        errors=["Could not parse reflection response as JSON"]
                    )
            
            # Extract insights
            analysis = agent_data.get('analysis', {})
            recommendations = agent_data.get('recommendations', {})
            
            # Apply profile updates if user profile exists
            profile_updates_made = []
            if user_profile and analysis.get('preference_updates'):
                preference_updates = analysis['preference_updates']
                
                # Update food preferences
                new_likes = preference_updates.get('new_likes', [])
                new_dislikes = preference_updates.get('new_dislikes', [])
                
                if new_likes:
                    for item in new_likes:
                        if item not in user_profile.food_preferences:
                            user_profile.food_preferences.append(item)
                            profile_updates_made.append(f"Added preference: {item}")
                
                if new_dislikes:
                    for item in new_dislikes:
                        if item not in user_profile.food_dislikes:
                            user_profile.food_dislikes.append(item)
                            profile_updates_made.append(f"Added dislike: {item}")
                        
                        # Remove from preferences if it was there
                        if item in user_profile.food_preferences:
                            user_profile.food_preferences.remove(item)
                            profile_updates_made.append(f"Removed conflicting preference: {item}")
                
                # Update cooking preferences
                cooking_style_prefs = preference_updates.get('cooking_style_preferences', [])
                timing_prefs = preference_updates.get('timing_preferences', [])
                
                # Apply cooking style updates (this would need more sophisticated logic)
                if cooking_style_prefs:
                    profile_updates_made.append(f"Noted cooking style preferences: {', '.join(cooking_style_prefs)}")
                
                # Save updated profile
                if profile_updates_made:
                    user_profile.updated_at = datetime.utcnow()
                    await db.save_user_profile(user_profile)
            
            # Store learning insights for future use
            learning_record = {
                'user_id': user_id,
                'timestamp': datetime.utcnow().isoformat(),
                'feedback_analysis': analysis,
                'recommendations': recommendations,
                'profile_updates_made': profile_updates_made,
                'confidence_score': agent_data.get('learning_summary', {}).get('confidence_in_analysis', 0.8)
            }
            
            # In a full implementation, you'd store this learning data
            # await self._store_learning_record(learning_record)
            
            return AgentResponse(
                agent_name=self.agent_name,
                success=True,
                data={
                    'analysis': analysis,
                    'recommendations': recommendations,
                    'profile_updates_made': profile_updates_made,
                    'learning_record': learning_record,
                    'next_steps': agent_data.get('next_steps', [])
                },
                confidence_score=agent_data.get('learning_summary', {}).get('confidence_in_analysis', 0.8)
            )
            
        except Exception as e:
            logger.error(f"Error processing learning insights: {str(e)}")
            return AgentResponse(
                agent_name=self.agent_name,
                success=False,
                errors=[f"Learning processing error: {str(e)}"]
            )
    
    async def analyze_usage_patterns(
        self,
        user_id: str,
        usage_data: Dict[str, Any]
    ) -> AgentResponse:
        """
        Analyze user usage patterns to identify behavioral insights
        """
        try:
            context_parts = []
            
            context_parts.append("## Usage Data:")
            context_parts.append(json.dumps(usage_data, indent=2))
            
            context_parts.append("\n## Analysis Request:")
            context_parts.append("Analyze user behavior patterns including:")
            context_parts.append("1. Frequency of meal plan requests")
            context_parts.append("2. Common modification patterns")
            context_parts.append("3. Time of day preferences for different meal types")
            context_parts.append("4. Inventory management habits")
            context_parts.append("5. Recipe complexity preferences over time")
            
            context = "\n".join(context_parts)
            
            response = await bedrock_client.invoke_with_retry(
                prompt=context,
                agent_name=self.agent_name,
                system_prompt=self.system_prompt,
                temperature=0.2
            )
            
            return response
            
        except Exception as e:
            logger.error(f"Error analyzing usage patterns: {str(e)}")
            return AgentResponse(
                agent_name=self.agent_name,
                success=False,
                errors=[f"Usage analysis error: {str(e)}"]
            )
    
    async def generate_personalization_recommendations(
        self,
        user_id: str,
        user_profile: UserProfile,
        recent_interactions: List[Dict[str, Any]]
    ) -> AgentResponse:
        """
        Generate specific personalization recommendations based on accumulated learning
        """
        try:
            context_parts = []
            
            context_parts.append("## User Profile:")
            context_parts.append(json.dumps(user_profile.to_dict(), indent=2))
            
            context_parts.append("\n## Recent Interactions:")
            for i, interaction in enumerate(recent_interactions[:5], 1):
                context_parts.append(f"### Interaction {i}:")
                context_parts.append(json.dumps(interaction, indent=2))
            
            context_parts.append("\n## Personalization Request:")
            context_parts.append("Based on the user profile and recent interactions, suggest:")
            context_parts.append("1. Specific meal planning algorithm adjustments")
            context_parts.append("2. Inventory management optimizations")
            context_parts.append("3. Communication style preferences")
            context_parts.append("4. Feature usage recommendations")
            context_parts.append("5. Proactive suggestions for this user")
            
            context = "\n".join(context_parts)
            
            system_prompt = """Generate personalization recommendations in JSON format:
{
  "algorithm_adjustments": [
    {
      "parameter": "parameter name",
      "current_value": "current setting",
      "recommended_value": "suggested setting",
      "reason": "why this change will help"
    }
  ],
  "communication_preferences": {
    "detail_level": "brief|moderate|detailed",
    "tone": "casual|professional|friendly",
    "notification_frequency": "high|medium|low"
  },
  "proactive_suggestions": [
    {
      "trigger": "when to suggest",
      "suggestion": "what to suggest",
      "expected_benefit": "why this helps the user"
    }
  ],
  "feature_recommendations": ["features this user would likely find valuable"]
}"""
            
            response = await bedrock_client.invoke_with_retry(
                prompt=context,
                agent_name=self.agent_name,
                system_prompt=system_prompt,
                temperature=0.2
            )
            
            return response
            
        except Exception as e:
            logger.error(f"Error generating personalization recommendations: {str(e)}")
            return AgentResponse(
                agent_name=self.agent_name,
                success=False,
                errors=[f"Personalization error: {str(e)}"]
            )
    
    def calculate_user_satisfaction_score(
        self,
        feedback_history: List[Dict[str, Any]]
    ) -> float:
        """
        Calculate a user satisfaction score based on feedback history
        """
        if not feedback_history:
            return 0.5  # Neutral score with no data
        
        try:
            total_score = 0
            weighted_count = 0
            
            # More recent feedback gets higher weight
            for i, feedback in enumerate(feedback_history):
                weight = 1.0 - (i * 0.1)  # Decreasing weight for older feedback
                weight = max(0.1, weight)  # Minimum weight
                
                # Extract satisfaction indicators
                score = 0.5  # Neutral default
                
                # Look for explicit ratings
                if 'rating' in feedback:
                    score = min(1.0, max(0.0, feedback['rating'] / 5.0))
                elif 'satisfaction' in feedback:
                    score = min(1.0, max(0.0, feedback['satisfaction'] / 5.0))
                else:
                    # Infer satisfaction from feedback content
                    content = str(feedback.get('feedback_text', '')).lower()
                    
                    positive_keywords = ['love', 'great', 'perfect', 'delicious', 'amazing', 'excellent']
                    negative_keywords = ['bad', 'terrible', 'hate', 'awful', 'disgusting', 'waste']
                    
                    positive_count = sum(1 for word in positive_keywords if word in content)
                    negative_count = sum(1 for word in negative_keywords if word in content)
                    
                    if positive_count > negative_count:
                        score = 0.7 + (positive_count * 0.1)
                    elif negative_count > positive_count:
                        score = 0.3 - (negative_count * 0.1)
                    
                    score = min(1.0, max(0.0, score))
                
                total_score += score * weight
                weighted_count += weight
            
            return total_score / weighted_count if weighted_count > 0 else 0.5
            
        except Exception as e:
            logger.error(f"Error calculating satisfaction score: {str(e)}")
            return 0.5

# Global reflection agent instance
reflection_agent = ReflectionAgent()