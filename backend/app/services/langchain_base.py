"""
Base LangChain infrastructure for xAI API integration
"""
import os
import json
import time
import logging
from typing import Any, Dict, List, Optional, Union
from pydantic import BaseModel, Field
import requests
from langchain_core.language_models.llms import LLM
from langchain_core.callbacks.manager import CallbackManagerForLLMRun
from langchain_core.outputs import LLMResult, Generation
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import BaseOutputParser
from flask import current_app

logger = logging.getLogger(__name__)

class XAIAPIError(Exception):
    """Custom exception for xAI API errors"""
    pass

class XAILLMConfig(BaseModel):
    """Configuration for xAI LLM"""
    api_key: str = Field(..., description="xAI API key")
    api_url: str = Field(default="https://api.x.ai/v1", description="xAI API base URL")
    model: str = Field(default="grok-3-mini", description="Model name")
    temperature: float = Field(default=0.7, description="Temperature for generation")
    max_tokens: int = Field(default=2500, description="Maximum tokens to generate")
    timeout: int = Field(default=90, description="Request timeout in seconds")
    max_retries: int = Field(default=5, description="Maximum number of retries")
    retry_delay: float = Field(default=2.0, description="Delay between retries in seconds")

class XAILLM(LLM):
    """Custom LangChain LLM for xAI API integration"""
    
    config: XAILLMConfig
    
    def __init__(self, **kwargs):
        # Get configuration from Flask app config or environment
        api_key = kwargs.get('api_key') or current_app.config.get('XAI_API_KEY') or os.getenv('XAI_API_KEY')
        api_url = kwargs.get('api_url') or current_app.config.get('GROK_API_URL') or os.getenv('GROK_API_URL', 'https://api.x.ai/v1')
        
        if not api_key:
            raise ValueError("XAI_API_KEY must be provided either as parameter, Flask config, or environment variable")
        
        config_data = {
            'api_key': api_key,
            'api_url': api_url,
            **kwargs
        }
        
        super().__init__(config=XAILLMConfig(**config_data))
    
    @property
    def _llm_type(self) -> str:
        return "xai"
    
    def _call(
        self,
        prompt: str,
        stop: Optional[List[str]] = None,
        run_manager: Optional[CallbackManagerForLLMRun] = None,
        **kwargs: Any,
    ) -> str:
        """Call the xAI API with retry logic and error handling"""
        
        headers = {
            "Authorization": f"Bearer {self.config.api_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": self.config.model,
            "messages": [
                {"role": "user", "content": prompt}
            ],
            "temperature": self.config.temperature,
            "max_tokens": self.config.max_tokens
        }
        
        # Add stop sequences if provided
        if stop:
            payload["stop"] = stop
        
        # Override config with any kwargs
        for key in ["temperature", "max_tokens"]:
            if key in kwargs:
                payload[key] = kwargs[key]
        
        last_error = None
        
        for attempt in range(self.config.max_retries):
            try:
                logger.debug(f"xAI API call attempt {attempt + 1}/{self.config.max_retries}")
                
                response = requests.post(
                    f"{self.config.api_url}/chat/completions",
                    headers=headers,
                    json=payload,
                    timeout=self.config.timeout
                )
                
                if response.status_code == 200:
                    result = response.json()
                    content = result["choices"][0]["message"]["content"]
                    logger.debug(f"xAI API call successful, response length: {len(content)}")
                    return content
                
                elif response.status_code == 429:  # Rate limit
                    wait_time = self.config.retry_delay * (2 ** attempt)
                    logger.warning(f"Rate limited, waiting {wait_time}s before retry")
                    time.sleep(wait_time)
                    last_error = XAIAPIError(f"Rate limited: {response.text}")
                    continue
                
                elif response.status_code >= 500:  # Server error
                    wait_time = self.config.retry_delay * (2 ** attempt)
                    logger.warning(f"Server error {response.status_code}, waiting {wait_time}s before retry")
                    time.sleep(wait_time)
                    last_error = XAIAPIError(f"Server error {response.status_code}: {response.text}")
                    continue
                
                else:  # Client error - don't retry
                    error_msg = f"API error {response.status_code}: {response.text}"
                    logger.error(error_msg)
                    raise XAIAPIError(error_msg)
                    
            except requests.exceptions.Timeout:
                wait_time = self.config.retry_delay * (2 ** attempt)
                logger.warning(f"Request timeout after {self.config.timeout}s, waiting {wait_time}s before retry (attempt {attempt + 1}/{self.config.max_retries})")
                time.sleep(wait_time)
                last_error = XAIAPIError(f"Request timeout after {self.config.timeout}s")
                continue
                
            except requests.exceptions.ConnectionError:
                wait_time = self.config.retry_delay * (2 ** attempt)
                logger.warning(f"Connection error, waiting {wait_time}s before retry")
                time.sleep(wait_time)
                last_error = XAIAPIError("Connection error")
                continue
                
            except Exception as e:
                logger.error(f"Unexpected error in xAI API call: {str(e)}")
                raise XAIAPIError(f"Unexpected error: {str(e)}")
        
        # All retries exhausted
        error_msg = f"All {self.config.max_retries} retries exhausted. Last error: {last_error}"
        logger.error(error_msg)
        raise XAIAPIError(error_msg)

class JSONOutputParser(BaseOutputParser[Dict[str, Any]]):
    """Parser for JSON output from LLM"""
    
    def parse(self, text: str) -> Dict[str, Any]:
        """Parse JSON from LLM output with improved error handling"""
        try:
            # Try to find JSON in the text
            text = text.strip()
            
            # Look for JSON block markers
            if "```json" in text:
                start = text.find("```json") + 7
                end = text.find("```", start)
                if end != -1:
                    text = text[start:end].strip()
            elif "```" in text:
                start = text.find("```") + 3
                end = text.find("```", start)
                if end != -1:
                    text = text[start:end].strip()
            
            # Try to parse as JSON
            return json.loads(text)
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON from LLM output: {e}")
            logger.error(f"JSON error at line {e.lineno}, column {e.colno}: {e.msg}")
            logger.error(f"Raw output length: {len(text)}")
            logger.error(f"Raw output (first 1000 chars): {text[:1000]}")
            logger.error(f"Raw output (last 1000 chars): {text[-1000:]}")
            
            # Log the specific problematic area
            if hasattr(e, 'pos') and e.pos:
                start = max(0, e.pos - 100)
                end = min(len(text), e.pos + 100)
                logger.error(f"Problematic area around position {e.pos}: {text[start:end]}")
            
            # Try to fix common JSON issues
            fixed_text = self._attempt_json_fix(text)
            if fixed_text != text:
                try:
                    logger.info("Attempting to parse fixed JSON")
                    logger.info(f"Fixed JSON (first 500 chars): {fixed_text[:500]}")
                    return json.loads(fixed_text)
                except json.JSONDecodeError as fix_error:
                    logger.error(f"Fixed JSON also failed to parse: {fix_error}")
            
            raise ValueError(f"Invalid JSON output from LLM: {e}")
    
    def _attempt_json_fix(self, text: str) -> str:
        """Attempt to fix common JSON formatting issues"""
        # Remove any trailing commas before closing brackets/braces
        import re
        
        # Fix trailing commas
        text = re.sub(r',(\s*[}\]])', r'\1', text)
        
        # If the JSON appears to be cut off, try to close it properly
        if text.count('{') > text.count('}'):
            # Add missing closing braces
            missing_braces = text.count('{') - text.count('}')
            text += '}' * missing_braces
            logger.info(f"Added {missing_braces} missing closing braces")
        
        if text.count('[') > text.count(']'):
            # Add missing closing brackets
            missing_brackets = text.count('[') - text.count(']')
            text += ']' * missing_brackets
            logger.info(f"Added {missing_brackets} missing closing brackets")
        
        # If there's an unterminated string at the end, try to close it
        if text.count('"') % 2 == 1:
            # Odd number of quotes - likely unterminated string
            text += '"'
            logger.info("Added missing closing quote")
        
        return text

class MarkdownOutputParser(BaseOutputParser[str]):
    """Parser for Markdown output from LLM"""
    
    def parse(self, text: str) -> str:
        """Parse and clean markdown from LLM output"""
        text = text.strip()
        
        # Remove markdown code block markers if present
        if text.startswith("```markdown"):
            text = text[11:].strip()
        elif text.startswith("```"):
            text = text[3:].strip()
        
        if text.endswith("```"):
            text = text[:-3].strip()
        
        return text

def validate_environment():
    """Validate that required environment variables are set"""
    errors = []
    
    api_key = current_app.config.get('XAI_API_KEY') or os.getenv('XAI_API_KEY')
    if not api_key:
        errors.append("XAI_API_KEY is not set")
    
    api_url = current_app.config.get('GROK_API_URL') or os.getenv('GROK_API_URL')
    if not api_url:
        # Set a default URL if not provided
        os.environ['GROK_API_URL'] = 'https://api.x.ai/v1'
        logger.info("GROK_API_URL not set, using default: https://api.x.ai/v1")
    
    if errors:
        error_msg = "Environment validation failed: " + ", ".join(errors)
        logger.warning(error_msg)  # Changed from error to warning
        # Don't raise an error, just log a warning for now
        # This allows the system to start even without API keys for testing
        return False
    
    logger.info("Environment validation passed")
    return True

def test_xai_connection():
    """Test connection to xAI API"""
    try:
        validate_environment()
        
        llm = XAILLM(temperature=0.1, max_tokens=50)
        response = llm._call("Say 'Hello, this is a test' and nothing else.")
        
        logger.info(f"xAI connection test successful: {response}")
        return True, response
        
    except Exception as e:
        logger.error(f"xAI connection test failed: {str(e)}")
        return False, str(e)