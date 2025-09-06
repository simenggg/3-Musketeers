import json
import logging
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timedelta
from enum import Enum
from dataclasses import dataclass
import asyncio

from models import AgentResponse, UserProfile, MealPlan, Recipe
from bedrock_client import bedrock_client
from database import db

logger = logging.getLogger(__name__)

class WorkflowStatus(Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    PARTIAL_SUCCESS = "partial_success"

class AgentType(Enum):
    MEAL_PLANNER = "meal_planner"
    INVENTORY_MANAGER = "inventory_manager"
    NUTRITION_ANALYZER = "nutrition_analyzer"
    RECIPE_GENERATOR = "recipe_generator"
    SHOPPING_LIST = "shopping_list"
    REFLECTION = "reflection"

@dataclass
class WorkflowStep:
    agent_type: AgentType
    priority: int
    dependencies: List[AgentType]
    required: bool = True
    timeout_seconds: int = 30

class MealPlanningOrchestrator:
    """
    Main orchestrator class that coordinates all agents in the meal planning system
    """
    
    def __init__(self):
        self.system_name = "MealPlanningOrchestrator"
        self.agents = self._initialize_agents()
        self.workflow_definitions = self._define_workflows()
        
    def _initialize_agents(self) -> Dict[AgentType, Any]:
        """Initialize all agent instances"""
        # Import agents here to avoid circular dependencies
        from meal_planner_agent import meal_planner_agent
        from inventory_agent import inventory_agent
        from nutrition_agent import nutrition_agent
        from recipe_agent import recipe_agent
        from shopping_list_agent import shopping_list_agent
        from reflection_agent import reflection_agent
        
        return {
            AgentType.MEAL_PLANNER: meal_planner_agent,
            AgentType.INVENTORY_MANAGER: inventory_agent,
            AgentType.NUTRITION_ANALYZER: nutrition_agent,
            AgentType.RECIPE_GENERATOR: recipe_agent,
            AgentType.SHOPPING_LIST: shopping_list_agent,
            AgentType.REFLECTION: reflection_agent
        }
    
    def _define_workflows(self) -> Dict[str, List[WorkflowStep]]:
        """Define different workflow patterns for various use cases"""
        return {
            "full_meal_plan": [
                WorkflowStep(AgentType.INVENTORY_MANAGER, 1, [], True, 15),
                WorkflowStep(AgentType.MEAL_PLANNER, 2, [AgentType.INVENTORY_MANAGER], True, 45),
                WorkflowStep(AgentType.NUTRITION_ANALYZER, 3, [AgentType.MEAL_PLANNER], False, 30),
                WorkflowStep(AgentType.SHOPPING_LIST, 4, [AgentType.MEAL_PLANNER, AgentType.INVENTORY_MANAGER], True, 20),
                WorkflowStep(AgentType.REFLECTION, 5, [AgentType.MEAL_PLANNER], False, 10)
            ],
            "quick_recipe": [
                WorkflowStep(AgentType.RECIPE_GENERATOR, 1, [], True, 30),
                WorkflowStep(AgentType.NUTRITION_ANALYZER, 2, [AgentType.RECIPE_GENERATOR], False, 20),
                WorkflowStep(AgentType.INVENTORY_MANAGER, 3, [AgentType.RECIPE_GENERATOR], False, 10)
            ],
            "inventory_update": [
                WorkflowStep(AgentType.INVENTORY_MANAGER, 1, [], True, 20),
                WorkflowStep(AgentType.MEAL_PLANNER, 2, [AgentType.INVENTORY_MANAGER], False, 30),
                WorkflowStep(AgentType.SHOPPING_LIST, 3, [AgentType.INVENTORY_MANAGER], False, 15)
            ],
            "feedback_learning": [
                WorkflowStep(AgentType.REFLECTION, 1, [], True, 25)
            ]
        }
    
    async def execute_meal_planning_workflow(
        self,
        user_id: str,
        request_data: Dict[str, Any],
        workflow_type: str = "full_meal_plan"
    ) -> Dict[str, Any]:
        """
        Execute the full meal planning workflow
        """
        workflow_id = f"{workflow_type}_{user_id}_{datetime.utcnow().timestamp()}"
        
        try:
            # Get user profile
            user_profile = await db.get_user_profile(user_id)
            if not user_profile:
                return {
                    "workflow_id": workflow_id,
                    "status": WorkflowStatus.FAILED.value,
                    "error": "User profile not found"
                }
            
            # Initialize workflow tracking
            workflow_state = {
                "workflow_id": workflow_id,
                "user_id": user_id,
                "workflow_type": workflow_type,
                "status": WorkflowStatus.IN_PROGRESS.value,
                "start_time": datetime.utcnow(),
                "agent_results": {},
                "errors": [],
                "warnings": []
            }
            
            # Get workflow definition
            workflow_steps = self.workflow_definitions.get(workflow_type)
            if not workflow_steps:
                return {
                    "workflow_id": workflow_id,
                    "status": WorkflowStatus.FAILED.value,
                    "error": f"Unknown workflow type: {workflow_type}"
                }
            
            # Execute workflow steps
            results = await self._execute_workflow_steps(
                workflow_steps, user_profile, request_data, workflow_state
            )
            
            # Process final results
            final_result = await self._process_workflow_results(
                results, workflow_state, user_profile
            )
            
            # Store workflow execution data for learning
            await self._store_workflow_execution(workflow_state, final_result)
            
            return final_result
            
        except Exception as e:
            logger.error(f"Error in meal planning workflow {workflow_id}: {str(e)}")
            return {
                "workflow_id": workflow_id,
                "status": WorkflowStatus.FAILED.value,
                "error": f"Workflow execution error: {str(e)}"
            }
    
    async def _execute_workflow_steps(
        self,
        workflow_steps: List[WorkflowStep],
        user_profile: UserProfile,
        request_data: Dict[str, Any],
        workflow_state: Dict[str, Any]
    ) -> Dict[AgentType, AgentResponse]:
        """
        Execute workflow steps with dependency management and parallel processing
        """
        results = {}
        completed_agents = set()
        
        # Sort steps by priority
        sorted_steps = sorted(workflow_steps, key=lambda x: x.priority)
        
        for step in sorted_steps:
            try:
                # Check if dependencies are met
                if not all(dep in completed_agents for dep in step.dependencies):
                    missing_deps = [dep for dep in step.dependencies if dep not in completed_agents]
                    error_msg = f"Dependencies not met for {step.agent_type.value}: {missing_deps}"
                    
                    if step.required:
                        workflow_state["errors"].append(error_msg)
                        continue
                    else:
                        workflow_state["warnings"].append(error_msg)
                        continue
                
                # Execute agent
                agent_result = await self._execute_agent_step(
                    step, user_profile, request_data, results, workflow_state
                )
                
                results[step.agent_type] = agent_result
                
                if agent_result.success:
                    completed_agents.add(step.agent_type)
                elif step.required:
                    error_msg = f"Required agent {step.agent_type.value} failed: {agent_result.errors}"
                    workflow_state["errors"].append(error_msg)
                else:
                    warning_msg = f"Optional agent {step.agent_type.value} failed: {agent_result.errors}"
                    workflow_state["warnings"].append(warning_msg)
                
                # Update workflow state
                workflow_state["agent_results"][step.agent_type.value] = {
                    "success": agent_result.success,
                    "confidence_score": agent_result.confidence_score,
                    "execution_time": agent_result.processing_time,
                    "data_size": len(str(agent_result.data)) if agent_result.data else 0
                }
                
            except asyncio.TimeoutError:
                error_msg = f"Agent {step.agent_type.value} timed out after {step.timeout_seconds}s"
                if step.required:
                    workflow_state["errors"].append(error_msg)
                else:
                    workflow_state["warnings"].append(error_msg)
                
            except Exception as e:
                error_msg = f"Unexpected error in {step.agent_type.value}: {str(e)}"
                logger.error(error_msg)
                if step.required:
                    workflow_state["errors"].append(error_msg)
                else:
                    workflow_state["warnings"].append(error_msg)
        
        return results
    
    async def _execute_agent_step(
        self,
        step: WorkflowStep,
        user_profile: UserProfile,
        request_data: Dict[str, Any],
        previous_results: Dict[AgentType, AgentResponse],
        workflow_state: Dict[str, Any]
    ) -> AgentResponse:
        """
        Execute a single agent step with timeout and context building
        """
        agent = self.agents.get(step.agent_type)
        if not agent:
            return AgentResponse(
                agent_name=step.agent_type.value,
                success=False,
                errors=[f"Agent {step.agent_type.value} not found"]
            )
        
        # Build context for the agent based on previous results and request data
        agent_context = self._build_agent_context(
            step.agent_type, user_profile, request_data, previous_results
        )
        
        # Execute with timeout
        try:
            start_time = datetime.utcnow()
            
            if step.agent_type == AgentType.MEAL_PLANNER:
                result = await asyncio.wait_for(
                    agent.generate_meal_plan(
                        workflow_state["user_id"],
                        agent_context.get("meal_preferences", {}),
                        agent_context.get("available_ingredients"),
                        user_profile
                    ),
                    timeout=step.timeout_seconds
                )
            elif step.agent_type == AgentType.INVENTORY_MANAGER:
                result = await asyncio.wait_for(
                    agent.analyze_inventory(
                        workflow_state["user_id"],
                        agent_context.get("inventory_data", {})
                    ),
                    timeout=step.timeout_seconds
                )
            elif step.agent_type == AgentType.NUTRITION_ANALYZER:
                meal_plan_data = previous_results.get(AgentType.MEAL_PLANNER)
                if meal_plan_data and meal_plan_data.success:
                    result = await asyncio.wait_for(
                        agent.analyze_nutrition(
                            meal_plan_data.data,
                            user_profile
                        ),
                        timeout=step.timeout_seconds
                    )
                else:
                    result = AgentResponse(
                        agent_name=step.agent_type.value,
                        success=False,
                        errors=["No meal plan data available for nutrition analysis"]
                    )
            elif step.agent_type == AgentType.RECIPE_GENERATOR:
                result = await asyncio.wait_for(
                    agent.generate_recipe(
                        agent_context.get("recipe_request", {}),
                        user_profile
                    ),
                    timeout=step.timeout_seconds
                )
            elif step.agent_type == AgentType.SHOPPING_LIST:
                meal_plan_data = previous_results.get(AgentType.MEAL_PLANNER)
                inventory_data = previous_results.get(AgentType.INVENTORY_MANAGER)
                result = await asyncio.wait_for(
                    agent.generate_shopping_list(
                        meal_plan_data.data if meal_plan_data else {},
                        inventory_data.data if inventory_data else {},
                        user_profile
                    ),
                    timeout=step.timeout_seconds
                )
            elif step.agent_type == AgentType.REFLECTION:
                result = await asyncio.wait_for(
                    agent.analyze_user_feedback(
                        workflow_state["user_id"],
                        agent_context.get("feedback_data", {}),
                        agent_context.get("meal_plan_history"),
                        user_profile
                    ),
                    timeout=step.timeout_seconds
                )
            else:
                result = AgentResponse(
                    agent_name=step.agent_type.value,
                    success=False,
                    errors=[f"Unknown agent type: {step.agent_type.value}"]
                )
            
            # Add processing time
            result.processing_time = (datetime.utcnow() - start_time).total_seconds()
            return result
            
        except asyncio.TimeoutError:
            return AgentResponse(
                agent_name=step.agent_type.value,
                success=False,
                errors=[f"Agent timed out after {step.timeout_seconds} seconds"]
            )
    
    def _build_agent_context(
        self,
        agent_type: AgentType,
        user_profile: UserProfile,
        request_data: Dict[str, Any],
        previous_results: Dict[AgentType, AgentResponse]
    ) -> Dict[str, Any]:
        """
        Build context for agent execution based on workflow state
        """
        context = {
            "user_profile": user_profile,
            "request_data": request_data
        }
        
        if agent_type == AgentType.MEAL_PLANNER:
            context.update({
                "meal_preferences": request_data.get("preferences", {}),
                "dietary_restrictions": [dr.value for dr in user_profile.dietary_restrictions],
                "available_ingredients": previous_results.get(AgentType.INVENTORY_MANAGER, {}).get("data", {}).get("available_items", [])
            })
        elif agent_type == AgentType.NUTRITION_ANALYZER:
            meal_plan_result = previous_results.get(AgentType.MEAL_PLANNER)
            if meal_plan_result:
                context["meal_plan"] = meal_plan_result.data
        elif agent_type == AgentType.SHOPPING_LIST:
            context.update({
                "meal_plan": previous_results.get(AgentType.MEAL_PLANNER, {}).get("data"),
                "current_inventory": previous_results.get(AgentType.INVENTORY_MANAGER, {}).get("data")
            })
        elif agent_type == AgentType.REFLECTION:
            context.update({
                "feedback_data": request_data.get("feedback", {}),
                "meal_plan_history": request_data.get("meal_plan_history", [])
            })
        
        return context
    
    async def _process_workflow_results(
        self,
        agent_results: Dict[AgentType, AgentResponse],
        workflow_state: Dict[str, Any],
        user_profile: UserProfile
    ) -> Dict[str, Any]:
        """
        Process and consolidate workflow results
        """
        # Determine overall workflow status
        required_agents = [step.agent_type for step in self.workflow_definitions[workflow_state["workflow_type"]] if step.required]
        successful_required = [agent_type for agent_type in required_agents if agent_results.get(agent_type, {}).success]
        
        if len(successful_required) == len(required_agents) and not workflow_state["errors"]:
            status = WorkflowStatus.COMPLETED
        elif successful_required:
            status = WorkflowStatus.PARTIAL_SUCCESS
        else:
            status = WorkflowStatus.FAILED
        
        # Build consolidated result
        consolidated_result = {
            "workflow_id": workflow_state["workflow_id"],
            "status": status.value,
            "execution_time": (datetime.utcnow() - workflow_state["start_time"]).total_seconds(),
            "user_id": workflow_state["user_id"],
            "workflow_type": workflow_state["workflow_type"]
        }
        
        # Add successful agent results
        if AgentType.MEAL_PLANNER in agent_results and agent_results[AgentType.MEAL_PLANNER].success:
            consolidated_result["meal_plan"] = agent_results[AgentType.MEAL_PLANNER].data
        
        if AgentType.NUTRITION_ANALYZER in agent_results and agent_results[AgentType.NUTRITION_ANALYZER].success:
            consolidated_result["nutrition_analysis"] = agent_results[AgentType.NUTRITION_ANALYZER].data
        
        if AgentType.SHOPPING_LIST in agent_results and agent_results[AgentType.SHOPPING_LIST].success:
            consolidated_result["shopping_list"] = agent_results[AgentType.SHOPPING_LIST].data
        
        if AgentType.INVENTORY_MANAGER in agent_results and agent_results[AgentType.INVENTORY_MANAGER].success:
            consolidated_result["inventory_status"] = agent_results[AgentType.INVENTORY_MANAGER].data
        
        # Add metadata
        consolidated_result["metadata"] = {
            "agent_execution_summary": workflow_state["agent_results"],
            "warnings": workflow_state["warnings"],
            "errors": workflow_state["errors"],
            "confidence_scores": {
                agent_type.value: result.confidence_score 
                for agent_type, result in agent_results.items() 
                if result.success
            }
        }
        
        return consolidated_result
    
    async def _store_workflow_execution(
        self,
        workflow_state: Dict[str, Any],
        final_result: Dict[str, Any]
    ) -> None:
        """
        Store workflow execution data for analytics and learning
        """
        try:
            execution_record = {
                "workflow_id": workflow_state["workflow_id"],
                "user_id": workflow_state["user_id"],
                "workflow_type": workflow_state["workflow_type"],
                "start_time": workflow_state["start_time"].isoformat(),
                "execution_time": final_result["execution_time"],
                "status": final_result["status"],
                "agent_results": workflow_state["agent_results"],
                "errors": workflow_state["errors"],
                "warnings": workflow_state["warnings"],
                "created_at": datetime.utcnow().isoformat()
            }
            
            # Store in database (implementation depends on your DB structure)
            # await db.store_workflow_execution(execution_record)
            
        except Exception as e:
            logger.error(f"Error storing workflow execution: {str(e)}")
    
    async def process_user_feedback(
        self,
        user_id: str,
        feedback_data: Dict[str, Any],
        meal_plan_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Process user feedback and trigger learning workflow
        """
        try:
            # Enhanced feedback data with context
            enhanced_feedback = {
                **feedback_data,
                "meal_plan_id": meal_plan_id,
                "timestamp": datetime.utcnow().isoformat(),
                "feedback_source": feedback_data.get("source", "manual")
            }
            
            # Get recent meal plan history for context
            meal_plan_history = await db.get_user_meal_history(user_id, limit=5)
            
            # Execute feedback learning workflow
            result = await self.execute_meal_planning_workflow(
                user_id=user_id,
                request_data={
                    "feedback": enhanced_feedback,
                    "meal_plan_history": meal_plan_history
                },
                workflow_type="feedback_learning"
            )
            
            return result
            
        except Exception as e:
            logger.error(f"Error processing user feedback: {str(e)}")
            return {
                "success": False,
                "error": f"Feedback processing error: {str(e)}"
            }
    
    async def get_workflow_status(self, workflow_id: str) -> Dict[str, Any]:
        """
        Get the current status of a workflow execution
        """
        try:
            # In a real implementation, you'd query the database
            # execution_record = await db.get_workflow_execution(workflow_id)
            # return execution_record
            
            # Placeholder implementation
            return {
                "workflow_id": workflow_id,
                "status": "not_implemented",
                "message": "Workflow status tracking not yet implemented"
            }
            
        except Exception as e:
            logger.error(f"Error getting workflow status: {str(e)}")
            return {
                "workflow_id": workflow_id,
                "status": "error",
                "error": str(e)
            }
    
    def get_supported_workflows(self) -> List[str]:
        """
        Get list of supported workflow types
        """
        return list(self.workflow_definitions.keys())
    
    def get_workflow_definition(self, workflow_type: str) -> Optional[List[Dict[str, Any]]]:
        """
        Get the definition of a specific workflow
        """
        workflow_steps = self.workflow_definitions.get(workflow_type)
        if not workflow_steps:
            return None
        
        return [
            {
                "agent_type": step.agent_type.value,
                "priority": step.priority,
                "dependencies": [dep.value for dep in step.dependencies],
                "required": step.required,
                "timeout_seconds": step.timeout_seconds
            }
            for step in workflow_steps
        ]

# Global orchestrator instance
meal_planning_orchestrator = MealPlanningOrchestrator()
