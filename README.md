"""
# Some Good Food: A RecipeBot for Your Fridge

## 🍳 Overview

This project implements a RecipeBot agent that provides cooking recipes and meal ideas based on user preferences. The agent utilizes the Strands framework and integrates with various tools to enhance its capabilities.

## Goal
- To reduce **food wastage** through smarter meal planning.
- To reduce **pressure on households**, especially elderly and working adults.

## Feature:
- **Recipe Generation**: Provides recipes and cooking tips.
- **Expiry Priorization**: Recipe generated prioritize items that are expiring soon.
- **Dietary Preferences**: Considers user dietary restrictions and preferences.
- **Meal Planning**: Plan weekly meals to reduce food waste.


## 🏗️ Architecture

### Code Structure
```
src/
├── main.py                 # Entry point
├── models/                 # Data structures
├── services/               # Business logic
├── tools/                  # MCP tool definitions
├── agents/                 # AI agent orchestration
├── server/                 # MCP server setup
└── utils/                  # Helper functions
```

### Key Components

#### **Services Layer**
- `FridgeService`: Manages inventory, expiry tracking, categorization
- `RecipeService`: Handles recipe generation and meal planning
- `MemoryService`: User preferences and learning capabilities

#### **Models**
- `FridgeItem`: Represents food items with expiry intelligence
- `Recipe`: Recipe structure with metadata

#### **Agent System**
- `RecipeAgent`: Orchestrates AI responses with memory context
- Smart tool selection and context management
- Learning from user interactions

## 🚀 Features

### **Smart Fridge Management**
- Automatic food categorization
- Expiry date tracking with urgency levels
- Intelligent inventory merging

### **Agentic AI Capabilities**
- Context-aware recipe suggestions
- Multi-tool orchestration
- Memory-based personalization
- Learning from user behavior

### **Advanced Recipe Generation**
- Priority-based ingredient usage
- Web scraping for real recipes
- Dietary restriction compliance
- Skill-level appropriate instructions

### **Waste Reduction**
- Weekly meal planning
- Expiry-based prioritization

## 🧪 Testing Strategy

### **Accuracy Testing**
Unlike traditional ML metrics (Precision/Recall), we measure:
- **Recipe Relevance**: Do suggestions match available ingredients?
- **Preference Alignment**: Does AI learn user preferences?
- **Waste Reduction**: Are expiring ingredients prioritized?

### **Test Data Preparation**
- Synthetic fridge inventories with known expiry patterns
- User preference profiles with expected outcomes
- Recipe databases for comparison
- Edge cases (empty fridge, expired items, dietary restrictions)

### **Evaluation Metrics**
- **Ingredient Usage Rate**: % of available ingredients used in suggestions
- **Expiry Awareness**: % of critical ingredients prioritized
- **Preference Accuracy**: User preference adherence score
- **Response Quality**: Structured output validation

## 🛠️ Installation & Usage

### Prerequisites
- Python 3.10+
- uv or pip package manager
- virtual environment (recommended)

#### Installation
```bash
# Create and activate virtual environment
python -m venv venv
source venv/bin/activate  # On Mac
venv\Scripts\activate     # On Windows

# Install dependencies
pip install -r requirements.txt
```

### Running the Application

#### Command Line Interface
```bash
python -m src.main
```

#### Web UI (Streamlit)
```bash
# Option 1: Direct streamlit command
streamlit run streamlit_app.py

# Option 2: Using the runner script
python run_ui.py
```

The web UI will be available at http://localhost:8501

### Running Tests
```bash
python -m pytest tests/
python -m pytest tests/test_integration.py -v
```

## 💡 Business Value

### **Error Handling for Users**
- Clear, actionable error messages
- Graceful degradation when APIs fail
- User-friendly guidance for corrections

### **Scalability Considerations**
- Modular service architecture
- Configurable memory limits
- Efficient data structures

### **Real-world Application**
- Reduces household food waste
- Saves money through smart meal planning
- Teaches cooking skills progressively
- Adapts to changing dietary needs

## 🎯 Agentic AI Demonstration

This project showcases:
- **Multi-tool Orchestration**: Coordinating fridge, recipe, and web tools
- **Context Management**: Maintaining conversation state and user preferences
- **Learning Capabilities**: Adapting to user behavior over time
- **Smart Decision Making**: Prioritizing actions based on urgency and preferences

## 📊 Code Quality

- **Type Hints**: Full type coverage for maintainability
- **Documentation**: Comprehensive docstrings and comments
- **Error Handling**: Robust exception handling with user-friendly messages
- **Testing**: Unit, integration, and accuracy tests
- **Clean Architecture**: Single responsibility and dependency injection

## 🔮 Future Enhancements

- Integration with grocery delivery APIs
- Computer vision for automatic ingredient recognition
- Nutritional analysis and health tracking
- Social features for recipe sharing
- IoT integration with smart appliances

---

*This project demonstrates production-ready Agentic AI with clean architecture, comprehensive testing, and real business value.*

