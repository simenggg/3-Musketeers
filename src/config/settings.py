"""Application configuration settings."""

import os
from dataclasses import dataclass
from typing import Optional


@dataclass
class Settings:
    """Application settings configuration."""
    
    # Server settings
    server_host: str = "localhost"
    server_port: int = 8000
    
    # AI Model settings
    model_id: str = "us.amazon.nova-lite-v1:0"
    temperature: float = 0.7
    
    # Memory settings
    max_cooking_history: int = 50
    max_previous_recipes: int = 20
    
    # Fridge settings
    default_expiry_days: int = 7
    urgent_threshold_days: int = 3
    
    # Logging settings
    log_level: str = "INFO"
    log_file: Optional[str] = None
    
    # External API settings
    recipe_search_timeout: int = 10
    max_recipe_suggestions: int = 5
    
    @classmethod
    def from_env(cls) -> 'Settings':
        """Create settings from environment variables."""
        return cls(
            server_host=os.getenv("SERVER_HOST", "localhost"),
            server_port=int(os.getenv("SERVER_PORT", "8000")),
            model_id=os.getenv("MODEL_ID", "us.amazon.nova-lite-v1:0"),
            temperature=float(os.getenv("TEMPERATURE", "0.7")),
            max_cooking_history=int(os.getenv("MAX_COOKING_HISTORY", "50")),
            max_previous_recipes=int(os.getenv("MAX_PREVIOUS_RECIPES", "20")),
            default_expiry_days=int(os.getenv("DEFAULT_EXPIRY_DAYS", "7")),
            urgent_threshold_days=int(os.getenv("URGENT_THRESHOLD_DAYS", "3")),
            log_level=os.getenv("LOG_LEVEL", "INFO"),
            log_file=os.getenv("LOG_FILE"),
            recipe_search_timeout=int(os.getenv("RECIPE_SEARCH_TIMEOUT", "10")),
            max_recipe_suggestions=int(os.getenv("MAX_RECIPE_SUGGESTIONS", "5"))
        )


# Global settings instance
settings = Settings.from_env()