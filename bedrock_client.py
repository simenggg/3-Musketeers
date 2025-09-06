import json
import logging
import time
from typing import Dict, Any, Optional
from botocore.exceptions import ClientError

from config import config
from models import AgentResponse

logger = logging.getLogger(__name__)

class BedrockClient:
    """Client for interacting with AWS Bedrock runtime"""
    
    def __init__(self):
        self.client = config.bedrock_runtime
        self.default_params = config.get_bedrock_params()
    
    async def invoke_model(
        self, 
        prompt: str, 
        agent_name: str,
        system_prompt: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None
    ) -> AgentResponse:
        """
        Invoke Bedrock model with prompt and return structured response
        """
        start_time = time.time()
        
        try:
            # Prepare request body
            body = self.default_params['body'].copy()
            
            # Override defaults if provided
            if temperature is not None:
                body['temperature'] = temperature
            if max_tokens is not None:
                body['max_tokens'] = max_tokens
            
            # Build messages array
            messages = []
            if system_prompt:
                messages.append({
                    "role": "system",
                    "content": system_prompt
                })
            
            messages.append({
                "role": "user", 
                "content": prompt
            })
            
            body['messages'] = messages
            
            # Invoke the model
            response = self.client.invoke_model(
                modelId=self.default_params['modelId'],
                contentType=self.default_params['contentType'],
                accept=self.default_params['accept'],
                body=json.dumps(body)
            )
            
            # Parse response
            response_body = json.loads(response['body'].read())
            
            # Extract content from Claude's response format
            content = ""
            if 'content' in response_body and len(response_body['content']) > 0:
                content = response_body['content'][0].get('text', '')
            
            processing_time = time.time() - start_time
            
            # Try to parse JSON response if it looks like JSON
            parsed_data = {}
            confidence_score = 0.8  # Default confidence
            
            if content.strip().startswith('{') and content.strip().endswith('}'):
                try:
                    parsed_data = json.loads(content)
                    confidence_score = parsed_data.get('confidence_score', 0.8)
                except json.JSONDecodeError:
                    parsed_data = {'raw_response': content}
            else:
                parsed_data = {'raw_response': content}
            
            return AgentResponse(
                agent_name=agent_name,
                success=True,
                data=parsed_data,
                confidence_score=confidence_score,
                processing_time=processing_time
            )
            
        except ClientError as e:
            error_code = e.response['Error']['Code']
            error_message = e.response['Error']['Message']
            logger.error(f"Bedrock ClientError in {agent_name}: {error_code} - {error_message}")
            
            return AgentResponse(
                agent_name=agent_name,
                success=False,
                errors=[f"{error_code}: {error_message}"],
                processing_time=time.time() - start_time
            )
            
        except Exception as e:
            logger.error(f"Unexpected error in {agent_name}: {str(e)}")
            return AgentResponse(
                agent_name=agent_name,
                success=False,
                errors=[f"Unexpected error: {str(e)}"],
                processing_time=time.time() - start_time
            )
    
    async def invoke_with_retry(
        self, 
        prompt: str, 
        agent_name: str,
        max_retries: int = 3,
        **kwargs
    ) -> AgentResponse:
        """
        Invoke model with retry logic
        """
        last_response = None
        
        for attempt in range(max_retries):
            try:
                response = await self.invoke_model(prompt, agent_name, **kwargs)
                
                if response.success:
                    return response
                
                last_response = response
                
                # Exponential backoff
                if attempt < max_retries - 1:
                    wait_time = (2 ** attempt) * 1
                    logger.warning(f"Attempt {attempt + 1} failed for {agent_name}, retrying in {wait_time}s")
                    time.sleep(wait_time)
                    
            except Exception as e:
                logger.error(f"Retry attempt {attempt + 1} failed for {agent_name}: {str(e)}")
                if attempt == max_retries - 1:
                    return AgentResponse(
                        agent_name=agent_name,
                        success=False,
                        errors=[f"Max retries exceeded: {str(e)}"]
                    )
        
        return last_response or AgentResponse(
            agent_name=agent_name,
            success=False,
            errors=["Failed after all retry attempts"]
        )
    
    def validate_response_format(self, response: Dict[str, Any], expected_fields: list) -> bool:
        """
        Validate that response contains expected fields
        """
        for field in expected_fields:
            if field not in response:
                logger.warning(f"Missing expected field: {field}")
                return False
        return True
    
    def extract_json_from_response(self, content: str) -> Optional[Dict[str, Any]]:
        """
        Extract JSON from model response, handling common formatting issues
        """
        try:
            # Try direct parsing first
            return json.loads(content)
        except json.JSONDecodeError:
            pass
        
        # Try to find JSON within the response
        start_idx = content.find('{')
        end_idx = content.rfind('}')
        
        if start_idx != -1 and end_idx != -1 and end_idx > start_idx:
            try:
                json_str = content[start_idx:end_idx + 1]
                return json.loads(json_str)
            except json.JSONDecodeError:
                pass
        
        logger.warning("Could not extract valid JSON from response")
        return None

# Global Bedrock client instance
bedrock_client = BedrockClient()
