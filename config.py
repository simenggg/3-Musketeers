import os
from dataclasses import dataclass
from typing import Dict, Any
import boto3
from botocore.config import Config

@dataclass
class AWSConfig:
    """AWS configuration for Bedrock and other services"""
    region: str = "us-east-1"
    bedrock_runtime_region: str = "us-east-1"
    model_id: str = "anthropic.claude-3-sonnet-20240229-v1:0"
    max_tokens: int = 4000
    temperature: float = 0.1
    
@dataclass
class DatabaseConfig:
    """DynamoDB configuration"""
    user_profiles_table: str = "good_food_user_profiles"
    meal_history_table: str = "good_food_meal_history"
    inventory_table: str = "good_food_inventory"
    
@dataclass
class AppConfig:
    """Application configuration"""
    max_meal_plan_days: int = 7
    expiry_warning_days: int = 3
    max_retry_attempts: int = 3
    cache_ttl_hours: int = 24

class ConfigManager:
    """Centralized configuration management"""
    
    def __init__(self):
        self.aws_config = AWSConfig()
        self.db_config = DatabaseConfig()
        self.app_config = AppConfig()
        
        # Load from environment variables if available
        self._load_from_env()
        
        # Initialize AWS clients
        self._init_aws_clients()
    
    def _load_from_env(self):
        """Load configuration from environment variables"""
        self.aws_config.region = os.getenv('AWS_REGION', self.aws_config.region)
        self.aws_config.model_id = os.getenv('BEDROCK_MODEL_ID', self.aws_config.model_id)
        
        self.db_config.user_profiles_table = os.getenv(
            'USER_PROFILES_TABLE', 
            self.db_config.user_profiles_table
        )
        self.db_config.meal_history_table = os.getenv(
            'MEAL_HISTORY_TABLE', 
            self.db_config.meal_history_table
        )
        self.db_config.inventory_table = os.getenv(
            'INVENTORY_TABLE', 
            self.db_config.inventory_table
        )
    
    def _init_aws_clients(self):
        """Initialize AWS service clients"""
        config = Config(
            region_name=self.aws_config.region,
            retries={'max_attempts': 3}
        )
        
        self.bedrock_runtime = boto3.client(
            'bedrock-runtime',
            region_name=self.aws_config.bedrock_runtime_region,
            config=config
        )
        
        self.dynamodb = boto3.resource(
            'dynamodb',
            region_name=self.aws_config.region,
            config=config
        )
        
        self.dynamodb_client = boto3.client(
            'dynamodb',
            region_name=self.aws_config.region,
            config=config
        )
    
    def get_bedrock_params(self) -> Dict[str, Any]:
        """Get standardized Bedrock invocation parameters"""
        return {
            'modelId': self.aws_config.model_id,
            'contentType': 'application/json',
            'accept': 'application/json',
            'body': {
                'max_tokens': self.aws_config.max_tokens,
                'temperature': self.aws_config.temperature,
                'anthropic_version': 'bedrock-2023-05-31'
            }
        }

# Global configuration instance
config = ConfigManager()
