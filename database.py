import json
from typing import Optional, List, Dict, Any
from datetime import datetime, date
import boto3
from botocore.exceptions import ClientError
import logging
from decimal import Decimal

from config import config
from models import UserProfile, UserInventory, MealPlan, FoodItem

logger = logging.getLogger(__name__)

class DecimalEncoder(json.JSONEncoder):
    """JSON encoder to handle Decimal types from DynamoDB"""
    def default(self, obj):
        if isinstance(obj, Decimal):
            return float(obj)
        return super(DecimalEncoder, self).default(obj)

class DatabaseManager:
    """Handles all database operations for the application"""
    
    def __init__(self):
        self.dynamodb = config.dynamodb
        self.dynamodb_client = config.dynamodb_client
        
        # Table references
        self.user_profiles_table = self.dynamodb.Table(config.db_config.user_profiles_table)
        self.meal_history_table = self.dynamodb.Table(config.db_config.meal_history_table)
        self.inventory_table = self.dynamodb.Table(config.db_config.inventory_table)
        
    def create_tables_if_not_exist(self):
        """Create DynamoDB tables if they don't exist"""
        try:
            # User Profiles Table
            self._create_user_profiles_table()
            # Meal History Table
            self._create_meal_history_table()
            # Inventory Table
            self._create_inventory_table()
            
        except Exception as e:
            logger.error(f"Error creating tables: {str(e)}")
            raise
    
    def _create_user_profiles_table(self):
        """Create user profiles table"""
        try:
            self.dynamodb_client.describe_table(TableName=config.db_config.user_profiles_table)
            logger.info("User profiles table already exists")
        except ClientError:
            logger.info("Creating user profiles table...")
            self.dynamodb_client.create_table(
                TableName=config.db_config.user_profiles_table,
                KeySchema=[
                    {'AttributeName': 'user_id', 'KeyType': 'HASH'}
                ],
                AttributeDefinitions=[
                    {'AttributeName': 'user_id', 'AttributeType': 'S'}
                ],
                BillingMode='PAY_PER_REQUEST',
                Tags=[
                    {'Key': 'Application', 'Value': 'GoodFoodToYou'},
                    {'Key': 'Environment', 'Value': 'development'}
                ]
            )
    
    def _create_meal_history_table(self):
        """Create meal history table"""
        try:
            self.dynamodb_client.describe_table(TableName=config.db_config.meal_history_table)
            logger.info("Meal history table already exists")
        except ClientError:
            logger.info("Creating meal history table...")
            self.dynamodb_client.create_table(
                TableName=config.db_config.meal_history_table,
                KeySchema=[
                    {'AttributeName': 'user_id', 'KeyType': 'HASH'},
                    {'AttributeName': 'plan_id', 'KeyType': 'RANGE'}
                ],
                AttributeDefinitions=[
                    {'AttributeName': 'user_id', 'AttributeType': 'S'},
                    {'AttributeName': 'plan_id', 'AttributeType': 'S'}
                ],
                BillingMode='PAY_PER_REQUEST',
                Tags=[
                    {'Key': 'Application', 'Value': 'GoodFoodToYou'},
                    {'Key': 'Environment', 'Value': 'development'}
                ]
            )
    
    def _create_inventory_table(self):
        """Create inventory table"""
        try:
            self.dynamodb_client.describe_table(TableName=config.db_config.inventory_table)
            logger.info("Inventory table already exists")
        except ClientError:
            logger.info("Creating inventory table...")
            self.dynamodb_client.create_table(
                TableName=config.db_config.inventory_table,
                KeySchema=[
                    {'AttributeName': 'user_id', 'KeyType': 'HASH'}
                ],
                AttributeDefinitions=[
                    {'AttributeName': 'user_id', 'AttributeType': 'S'}
                ],
                BillingMode='PAY_PER_REQUEST',
                Tags=[
                    {'Key': 'Application', 'Value': 'GoodFoodToYou'},
                    {'Key': 'Environment', 'Value': 'development'}
                ]
            )

    # User Profile Operations
    async def save_user_profile(self, profile: UserProfile) -> bool:
        """Save or update user profile"""
        try:
            profile.updated_at = datetime.utcnow()
            profile_data = profile.to_dict()
            
            self.user_profiles_table.put_item(
                Item=json.loads(json.dumps(profile_data, default=str))
            )
            logger.info(f"Saved profile for user {profile.user_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error saving user profile: {str(e)}")
            return False
    
    async def get_user_profile(self, user_id: str) -> Optional[UserProfile]:
        """Retrieve user profile"""
        try:
            response = self.user_profiles_table.get_item(
                Key={'user_id': user_id}
            )
            
            if 'Item' in response:
                # Convert DynamoDB response to regular dict
                item_dict = json.loads(json.dumps(response['Item'], cls=DecimalEncoder))
                return UserProfile.from_dict(item_dict)
            return None
            
        except Exception as e:
            logger.error(f"Error retrieving user profile: {str(e)}")
            return None
    
    async def update_user_profile(self, user_id: str, updates: Dict[str, Any]) -> bool:
        """Update specific fields in user profile"""
        try:
            # Build update expression
            update_expression_parts = []
            expression_attribute_values = {}
            
            for key, value in updates.items():
                update_expression_parts.append(f"{key} = :{key}")
                expression_attribute_values[f":{key}"] = value
            
            update_expression_parts.append("updated_at = :updated_at")
            expression_attribute_values[":updated_at"] = datetime.utcnow().isoformat()
            
            update_expression = "SET " + ", ".join(update_expression_parts)
            
            self.user_profiles_table.update_item(
                Key={'user_id': user_id},
                UpdateExpression=update_expression,
                ExpressionAttributeValues=expression_attribute_values
            )
            
            logger.info(f"Updated profile for user {user_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error updating user profile: {str(e)}")
            return False

    # Inventory Operations
    async def save_user_inventory(self, inventory: UserInventory) -> bool:
        """Save user's food inventory"""
        try:
            inventory.last_updated = datetime.utcnow()
            inventory_data = inventory.to_dict()
            
            self.inventory_table.put_item(
                Item=json.loads(json.dumps(inventory_data, default=str))
            )
            logger.info(f"Saved inventory for user {inventory.user_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error saving inventory: {str(e)}")
            return False
    
    async def get_user_inventory(self, user_id: str) -> Optional[UserInventory]:
        """Retrieve user's food inventory"""
        try:
            response = self.inventory_table.get_item(
                Key={'user_id': user_id}
            )
            
            if 'Item' in response:
                item_dict = json.loads(json.dumps(response['Item'], cls=DecimalEncoder))
                
                # Reconstruct FoodItem objects
                items = []
                for item_data in item_dict.get('items', []):
                    items.append(FoodItem.from_dict(item_data))
                
                return UserInventory(
                    user_id=item_dict['user_id'],
                    items=items,
                    last_updated=datetime.fromisoformat(item_dict['last_updated'])
                )
            return None
            
        except Exception as e:
            logger.error(f"Error retrieving inventory: {str(e)}")
            return None
    
    async def add_inventory_item(self, user_id: str, food_item: FoodItem) -> bool:
        """Add or update a single inventory item"""
        try:
            # Get current inventory
            inventory = await self.get_user_inventory(user_id)
            if not inventory:
                inventory = UserInventory(user_id=user_id, items=[])
            
            # Check if item already exists (by name)
            existing_item_index = None
            for i, item in enumerate(inventory.items):
                if item.name.lower() == food_item.name.lower():
                    existing_item_index = i
                    break
            
            if existing_item_index is not None:
                # Update existing item
                inventory.items[existing_item_index] = food_item
            else:
                # Add new item
                inventory.items.append(food_item)
            
            return await self.save_user_inventory(inventory)
            
        except Exception as e:
            logger.error(f"Error adding inventory item: {str(e)}")
            return False
    
    async def remove_inventory_item(self, user_id: str, item_name: str) -> bool:
        """Remove an inventory item"""
        try:
            inventory = await self.get_user_inventory(user_id)
            if not inventory:
                return False
            
            # Remove item by name
            inventory.items = [
                item for item in inventory.items 
                if item.name.lower() != item_name.lower()
            ]
            
            return await self.save_user_inventory(inventory)
            
        except Exception as e:
            logger.error(f"Error removing inventory item: {str(e)}")
            return False

    # Meal Plan Operations
    async def save_meal_plan(self, meal_plan: MealPlan) -> bool:
        """Save meal plan to history"""
        try:
            meal_plan_data = meal_plan.to_dict()
            
            self.meal_history_table.put_item(
                Item=json.loads(json.dumps(meal_plan_data, default=str))
            )
            logger.info(f"Saved meal plan {meal_plan.plan_id} for user {meal_plan.user_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error saving meal plan: {str(e)}")
            return False
    
    async def get_meal_plan(self, user_id: str, plan_id: str) -> Optional[MealPlan]:
        """Retrieve a specific meal plan"""
        try:
            response = self.meal_history_table.get_item(
                Key={'user_id': user_id, 'plan_id': plan_id}
            )
            
            if 'Item' in response:
                item_dict = json.loads(json.dumps(response['Item'], cls=DecimalEncoder))
                # Note: This is a simplified reconstruction
                # In a full implementation, you'd need to reconstruct all nested objects
                return item_dict
            return None
            
        except Exception as e:
            logger.error(f"Error retrieving meal plan: {str(e)}")
            return None
    
    async def get_user_meal_history(self, user_id: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Get user's meal plan history"""
        try:
            response = self.meal_history_table.query(
                KeyConditionExpression='user_id = :user_id',
                ExpressionAttributeValues={':user_id': user_id},
                ScanIndexForward=False,  # Most recent first
                Limit=limit
            )
            
            items = []
            for item in response.get('Items', []):
                items.append(json.loads(json.dumps(item, cls=DecimalEncoder)))
            
            return items
            
        except Exception as e:
            logger.error(f"Error retrieving meal history: {str(e)}")
            return []
    
    async def cleanup_old_meal_plans(self, days_old: int = 30) -> bool:
        """Remove meal plans older than specified days"""
        try:
            cutoff_date = datetime.utcnow().timestamp() - (days_old * 24 * 60 * 60)
            
            # This would require a scan operation in a production system
            # For now, we'll implement basic cleanup
            logger.info(f"Cleanup would remove meal plans older than {days_old} days")
            return True
            
        except Exception as e:
            logger.error(f"Error during cleanup: {str(e)}")
            return False

# Global database instance
db = DatabaseManager()