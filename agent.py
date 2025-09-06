from strands import Agent
# from strands_tools import http_request
from dotenv import load_dotenv

load_dotenv()

recipe_agent = Agent(
    model="us.anthropic.claude-sonnet-4-20250514-v1:0",
    system_prompt="You are a RecipeBot, an expert in cooking and recipes. You can provide recipes, cooking tips, and meal ideas based on user preferences.",
)

response = recipe_agent("Suggest a recipe for a vegetarian dinner with ingredients I have at home.")

print(response)