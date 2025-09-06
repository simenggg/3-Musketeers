# Good Food For You: A RecipeBot for Your Fridge

This project implements a RecipeBot agent that provides cooking recipes and meal ideas based on user preferences. The agent utilizes the Strands framework and integrates with various tools to enhance its capabilities.

## Goal
- To reduce **food wastage** through smarter meal planning.
- To reduce **pressure on households**, especially elderly and working adults.
- To promote **healthy eating habits** by providing nutritious recipes.

## Feature
- **Recipe Generation**: Provides recipes and cooking tips.
- **Expiry Priorization**: Recipe generated prioritize items that are expiring soon.
- **Dietary Preferences**: Considers user dietary restrictions and preferences.

## Tech Stack
- **Language Model**: Anthropic Claude Sonnet 4 via Amazon Bedrock.
- **Framework**: Strands Agents and Tools.

## Prerequisites
- Python 3.10+
- uv or pip package manager
- virtual environment (recommended)

### Installation
```bash
# Create and activate virtual environment
python -m venv venv
source venv/bin/activate  # On Mac
venv\Scripts\activate     # On Windows

# Install dependencies
pip install -r requirements.txt
```