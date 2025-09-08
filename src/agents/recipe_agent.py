"""Recipe Assistant Agent with advanced orchestration."""

from strands import Agent
from strands.models import BedrockModel
from strands.tools.mcp.mcp_client import MCPClient

from ..services.memory_service import MemoryService


class RecipeAgent:
    """Intelligent recipe assistant agent with memory and learning."""
    
    def __init__(self, mcp_client: MCPClient, memory_service: MemoryService):
        self.memory_service = memory_service
        
        # Get tools from MCP server
        tools = mcp_client.list_tools_sync()
        
        # Initialize agent with enhanced system prompt
        self.agent = Agent(
            model=BedrockModel(model_id="us.amazon.nova-lite-v1:0", temperature=0.7),
            system_prompt=self._get_system_prompt(),
            tools=tools,
            callback_handler=None
        )
        
        print(f"🔧 Advanced tools loaded: {[t.tool_name for t in tools]}")
    
    def process_user_input(self, user_input: str) -> str:
        """Process user input with memory context."""
        # Add memory context to user input
        memory_context = self.memory_service.get_memory_context()
        full_prompt = f"[MEMORY: {memory_context}] {user_input}" if memory_context else user_input
        
        # Get response from agent
        response = self.agent(full_prompt)
        
        try:
            reply = response.messages[-1].content[0].text
        except:
            reply = str(response)
        
        # Track interaction in memory
        self._update_memory(user_input, reply)
        
        return reply
    
    def _update_memory(self, user_input: str, reply: str):
        """Update memory with interaction data."""
        # Track cooking sessions
        if any(word in user_input.lower() for word in ['recipe', 'cook', 'dinner', 'lunch', 'breakfast']):
            self.memory_service.add_cooking_session(user_input, len(reply))
        
        # Track recipes
        if "🍽️" in reply:
            recipe_name = self.memory_service.extract_recipe_name_from_response(reply)
            self.memory_service.add_recipe(recipe_name, user_input, reply)
    
    def setup_user_profile(self, dietary: str, dislikes: str, cuisines: str, skill: str):
        """Setup user profile during initialization."""
        dislikes_list = [d.strip() for d in dislikes.split(",")] if dislikes else []
        cuisines_list = [c.strip() for c in cuisines.split(",")] if cuisines else []
        
        self.memory_service.update_profile(
            dietary_restrictions=dietary,
            dislikes=dislikes_list,
            favorite_cuisines=cuisines_list,
            cooking_skill=skill or "beginner"
        )
    
    def get_session_stats(self) -> dict:
        """Get session statistics."""
        return self.memory_service.get_profile_summary()
    
    def _get_system_prompt(self) -> str:
        """Get comprehensive system prompt for the agent."""
        return """You are an intelligent and helpful fridge management assistant 🍳🧠

You are a master at:
1. **Fridge Management:** Track inventory with expiry intelligence
2. **Recipe Suggestions:** Create recipes prioritizing expiring ingredients
3. **Meal Planning:** Weekly planning to minimize food waste
4. **Smart Orchestration:** Coordinate between all tools seamlessly

You can:
1. Make http request to various websites to gather recipe information
2. Process and analyze recipe information and choose the most suitable ones based on the ingredients the user have and the user's eating preferences (e.g. vegetarian, vegan, low-carb, halal, no dairy, etc.)
3. Provide 5 recipes based on the ingredients the user have
4. Track cooking history to avoid repetition

When retrieving recipes, follow these guidelines:
1. Suggest recipes by visiting https://www.allrecipes.com/ or https://www.recipetineats.com/ based on the ingredients the user has
2. Be creative, but stick to the available ingredients

When providing recipes, ensure you:
1. List all ingredients needed
2. Provide simple, step-by-step instructions
3. Suggest optional additional ingredients if necessary, but clearly mark them as optional
4. Keep responses concise, clear, and beginner-friendly

## MEMORY & LEARNING:
You have access to user preferences, cooking history, and patterns.
Use this to personalize all interactions and learn from user behavior.

## EXPIRY PRIORITIZATION SYSTEM:
🔴 **CRITICAL** (0-1 days): Must use immediately
🟡 **URGENT** (2-3 days): Use very soon
🟢 **UPCOMING** (4-7 days): Plan to use
✅ **FRESH** (8+ days): Good for later

## ORCHESTRATION INTELLIGENCE:
When users ask for recipes:
1. First check expiring items (get_expiring_items)
2. Get available ingredients (list_items)
3. Generate recipes prioritizing urgent ingredients
4. Optionally search online for real recipes
5. Consider user's cooking history and preferences

## RECIPE FORMAT:
🍽️ **[Recipe Name]** [Difficulty: Easy/Medium/Hard]
⏰ Prep: X min | Cook: X min | Serves: X
🎯 **Priority:** Uses [expiring ingredients]

**Ingredients:**
✅ From your fridge: [list with expiry status]
🛒 Need to buy: [optional ingredients]

**Instructions:**
1. [Clear, numbered steps]
2. [Beginner-friendly language]

## PERSONALIZATION:
- Proactive about expiry management
- Enthusiastic about reducing food waste
- Educational about cooking techniques
- Encouraging and supportive
- Memory-aware (reference past conversations)

Always think strategically about ingredient usage and meal planning!
"""