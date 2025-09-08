"""Main entry point for the Recipe Assistant application."""

import threading
import time
from datetime import datetime
from mcp.client.streamable_http import streamablehttp_client
from strands.tools.mcp.mcp_client import MCPClient

from .server.mcp_server import start_advanced_fridge_server
from .services.fridge_service import FridgeService
from .services.recipe_service import RecipeService
from .services.memory_service import MemoryService
from .agents.recipe_agent import RecipeAgent
from .utils.logging_config import disable_logging, setup_logging
from .config.settings import settings


def main():
    """Enhanced main function with advanced orchestration."""
    # Setup logging (disable for cleaner demo output)
    disable_logging()
    
    print("\n🍳 Recipe Assistant Agent\n")
    print("Welcome to the Recipe Assistant!")
    
    # Initialize services
    fridge_service = FridgeService()
    recipe_service = RecipeService()
    memory_service = MemoryService()
    
    # Start advanced server
    server_thread = threading.Thread(
        target=start_advanced_fridge_server, 
        args=(fridge_service, recipe_service),
        daemon=True
    )
    server_thread.start()
    
    # Wait for server to start
    time.sleep(3)
    
    # Connect to server
    def create_transport():
        return streamablehttp_client(f"http://{settings.server_host}:{settings.server_port}/mcp/")
    
    mcp_client = MCPClient(create_transport)
    
    # Connect and create advanced agent
    with mcp_client:
        # Initialize agent
        agent = RecipeAgent(mcp_client, memory_service)
        
        # Enhanced setup process
        print("\n" + "="*70)
        print("🍳 ADVANCED RECIPE ASSISTANT - AI Chef & Waste Reducer")
        print("="*70)
        print("I'm your smart cooking companion! I help you:")
        print("• Manage fridge inventory with expiry intelligence")
        print("• Create recipes that prioritize expiring ingredients")
        print("• Plan weekly meals to reduce food waste")
        print("• Learn your preferences and cooking patterns")
        
        # User profile setup
        setup_user_profile(agent)
        
        # Main interaction loop
        run_interaction_loop(agent)


def setup_user_profile(agent: RecipeAgent):
    """Setup user profile with preferences."""
    print("\n🎯 Let's personalize your cooking experience:")
    
    try:
        dietary = input("🥘 Dietary restrictions (vegetarian, vegan, keto, etc.): ").strip()
        dislikes = input("🚫 Foods you avoid (comma separated): ").strip()
        cuisines = input("🌍 Favorite cuisines (Italian, Asian, Mexican, etc.): ").strip()
        skill = input("👨‍🍳 Cooking skill (beginner/intermediate/advanced): ").strip() or "beginner"
        
        # Setup profile
        agent.setup_user_profile(dietary, dislikes, cuisines, skill)
        
        print(f"\n✅ Profile created! Skill level: {skill}")
        print("🧠 I'll remember your preferences and learn from our cooking sessions!")
        print("Tell me what ingredients you have, and I'll suggest a recipe!")
        print("\nType 'exit' to quit.\n")
        
    except KeyboardInterrupt:
        print("\n👋 Setup cancelled. Using default preferences.")


def run_interaction_loop(agent: RecipeAgent):
    """Main interaction loop with the user."""
    while True:
        try:
            user_input = input("💬 You: ").strip()
            
            if user_input.lower() in ["exit", "quit", "bye"]:
                show_session_summary(agent)
                break
            
            if not user_input:
                print("🤖 Ready to help with your fridge or cooking! What's on your mind? 😊")
                continue
            
            # Process user input through agent
            print("🤖 Assistant: ", end="")
            response = agent.process_user_input(user_input)
            print(response)
            print()
            
        except KeyboardInterrupt:
            print("\n🤖 Thanks for cooking with me! 👋")
            break
        except Exception as e:
            print(f"🤖 Oops! Something went wrong: {e}")
            print("Let's keep cooking! 😊")


def show_session_summary(agent: RecipeAgent):
    """Show session statistics and goodbye message."""
    try:
        stats = agent.get_session_stats()
        print(f"\n🎉 Great cooking session!")
        print(f"📊 Session Stats:")
        print(f"   • Recipes suggested: {stats['recipes_tried']}")
        print(f"   • Cooking sessions: {stats['sessions_completed']}")
        print(f"   • Skill level: {stats['cooking_skill']}")
        
        if stats['favorite_cuisines']:
            print(f"   • Favorite cuisines: {', '.join(stats['favorite_cuisines'])}")
        
        print("👋 Happy cooking!")
    except Exception:
        print("\n🎉 Great cooking session!")
        print("👋 Happy cooking!")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nExiting...")