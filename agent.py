<<<<<<< HEAD
from dotenv import load_dotenv
from strands import Agent, tool
from strands_tools import calculator, current_time

load_dotenv(".env.example")

# Define a custom tool as a Python function using the @tool decorator
@tool
def letter_counter(word: str, letter: str) -> int:
    """
    Count occurrences of a specific letter in a word.

    Args:
        word (str): The input word to search in
        letter (str): The specific letter to count

    Returns:
        int: The number of occurrences of the letter in the word
    """
    if not isinstance(word, str) or not isinstance(letter, str):
        return 0

    if len(letter) != 1:
        raise ValueError("The 'letter' parameter must be a single character")

    return word.lower().count(letter.lower())

# Create an agent with tools from the community-driven strands-tools package
# as well as our custom letter_counter tool
agent = Agent(tools=[calculator, current_time, letter_counter])

# Ask the agent a question that uses the available tools
message = """
I have 4 requests:

1. What is the time right now?
2. Calculate 3111696 / 74088
3. Tell me how many letter R's are in the word "strawberry" 🍓
"""
agent(message)
=======
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
>>>>>>> 6a992a5ebe80b831c53a0435843389b60dc215ca
