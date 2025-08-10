"""
Unit tests for LangChain infrastructure
"""
import pytest
import os
import json
from unittest.mock import Mock, patch, MagicMock
from app.services.langchain_base import (
    XAILLM, 
    XAILLMConfig, 
    XAIAPIError,
    JSONOutputParser,
    MarkdownOutputParser,
    validate_environment,
    test_xai_connection
)
from app.services.langchain_chains import (
    SurveyGenerationChain,
    BaseLangChainService
)
from app.services.langchain_pipeline import LangChainPipelineService

class TestXAILLMConfig:
    """Test XAI LLM configuration"""
    
    def test_config_creation_with_defaults(self):
        """Test creating config with default values"""
        config = XAILLMConfig(api_key="test-key")
        
        assert config.api_key == "test-key"
        assert config.api_url == "https://api.x.ai/v1"
        assert config.model == "grok-3-mini"
        assert config.temperature == 0.7
        assert config.max_tokens == 2000
        assert config.timeout == 60
        assert config.max_retries == 3
        assert config.retry_delay == 1.0
    
    def test_config_creation_with_custom_values(self):
        """Test creating config with custom values"""
        config = XAILLMConfig(
            api_key="custom-key",
            api_url="https://custom.api.com",
            model="custom-model",
            temperature=0.5,
            max_tokens=1000,
            timeout=30,
            max_retries=5,
            retry_delay=2.0
        )
        
        assert config.api_key == "custom-key"
        assert config.api_url == "https://custom.api.com"
        assert config.model == "custom-model"
        assert config.temperature == 0.5
        assert config.max_tokens == 1000
        assert config.timeout == 30
        assert config.max_retries == 5
        assert config.retry_delay == 2.0

class TestXAILLM:
    """Test XAI LLM implementation"""
    
    @patch('app.services.langchain_base.current_app')
    def test_llm_initialization_with_app_config(self, mock_app):
        """Test LLM initialization using Flask app config"""
        mock_app.config = {
            'XAI_API_KEY': 'app-config-key',
            'GROK_API_URL': 'https://app-config.api.com'
        }
        
        llm = XAILLM()
        
        assert llm.config.api_key == 'app-config-key'
        assert llm.config.api_url == 'https://app-config.api.com'
    
    @patch.dict(os.environ, {'XAI_API_KEY': 'env-key', 'GROK_API_URL': 'https://env.api.com'})
    @patch('app.services.langchain_base.current_app')
    def test_llm_initialization_with_env_vars(self, mock_app):
        """Test LLM initialization using environment variables"""
        mock_app.config = {}
        
        llm = XAILLM()
        
        assert llm.config.api_key == 'env-key'
        assert llm.config.api_url == 'https://env.api.com'
    
    @patch('app.services.langchain_base.current_app')
    def test_llm_initialization_without_api_key_raises_error(self, mock_app):
        """Test that missing API key raises ValueError"""
        mock_app.config = {}
        
        with patch.dict(os.environ, {}, clear=True):
            with pytest.raises(ValueError, match="XAI_API_KEY must be provided"):
                XAILLM()
    
    @patch('app.services.langchain_base.current_app')
    @patch('app.services.langchain_base.requests.post')
    def test_successful_api_call(self, mock_post, mock_app):
        """Test successful API call"""
        mock_app.config = {'XAI_API_KEY': 'test-key'}
        
        # Mock successful response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "choices": [{"message": {"content": "Test response"}}]
        }
        mock_post.return_value = mock_response
        
        llm = XAILLM()
        result = llm._call("Test prompt")
        
        assert result == "Test response"
        mock_post.assert_called_once()
    
    @patch('app.services.langchain_base.current_app')
    @patch('app.services.langchain_base.requests.post')
    def test_api_call_with_rate_limit_retry(self, mock_post, mock_app):
        """Test API call with rate limit and successful retry"""
        mock_app.config = {'XAI_API_KEY': 'test-key'}
        
        # Mock rate limit response followed by success
        rate_limit_response = Mock()
        rate_limit_response.status_code = 429
        rate_limit_response.text = "Rate limited"
        
        success_response = Mock()
        success_response.status_code = 200
        success_response.json.return_value = {
            "choices": [{"message": {"content": "Success after retry"}}]
        }
        
        mock_post.side_effect = [rate_limit_response, success_response]
        
        llm = XAILLM()
        with patch('time.sleep'):  # Mock sleep to speed up test
            result = llm._call("Test prompt")
        
        assert result == "Success after retry"
        assert mock_post.call_count == 2
    
    @patch('app.services.langchain_base.current_app')
    @patch('app.services.langchain_base.requests.post')
    def test_api_call_exhausts_retries(self, mock_post, mock_app):
        """Test API call that exhausts all retries"""
        mock_app.config = {'XAI_API_KEY': 'test-key'}
        
        # Mock consistent rate limit responses
        rate_limit_response = Mock()
        rate_limit_response.status_code = 429
        rate_limit_response.text = "Rate limited"
        mock_post.return_value = rate_limit_response
        
        llm = XAILLM()
        with patch('time.sleep'):  # Mock sleep to speed up test
            with pytest.raises(XAIAPIError, match="All 3 retries exhausted"):
                llm._call("Test prompt")
        
        assert mock_post.call_count == 3

class TestOutputParsers:
    """Test output parser implementations"""
    
    def test_json_parser_with_clean_json(self):
        """Test JSON parser with clean JSON input"""
        parser = JSONOutputParser()
        json_text = '{"key": "value", "number": 42}'
        
        result = parser.parse(json_text)
        
        assert result == {"key": "value", "number": 42}
    
    def test_json_parser_with_markdown_blocks(self):
        """Test JSON parser with markdown code blocks"""
        parser = JSONOutputParser()
        json_text = '''
        Here's the JSON:
        ```json
        {"key": "value", "number": 42}
        ```
        '''
        
        result = parser.parse(json_text)
        
        assert result == {"key": "value", "number": 42}
    
    def test_json_parser_with_invalid_json_raises_error(self):
        """Test JSON parser with invalid JSON raises ValueError"""
        parser = JSONOutputParser()
        invalid_json = '{"key": "value", "number":}'
        
        with pytest.raises(ValueError, match="Invalid JSON output"):
            parser.parse(invalid_json)
    
    def test_markdown_parser_with_clean_markdown(self):
        """Test markdown parser with clean markdown"""
        parser = MarkdownOutputParser()
        markdown_text = "# Title\n\nSome content"
        
        result = parser.parse(markdown_text)
        
        assert result == "# Title\n\nSome content"
    
    def test_markdown_parser_with_code_blocks(self):
        """Test markdown parser with code block markers"""
        parser = MarkdownOutputParser()
        markdown_text = '''```markdown
# Title

Some content
```'''
        
        result = parser.parse(markdown_text)
        
        assert result == "# Title\n\nSome content"

class TestEnvironmentValidation:
    """Test environment validation functions"""
    
    @patch('app.services.langchain_base.current_app')
    def test_validate_environment_success(self, mock_app):
        """Test successful environment validation"""
        mock_app.config = {
            'XAI_API_KEY': 'test-key',
            'GROK_API_URL': 'https://test.api.com'
        }
        
        result = validate_environment()
        
        assert result is True
    
    @patch('app.services.langchain_base.current_app')
    def test_validate_environment_missing_api_key(self, mock_app):
        """Test environment validation with missing API key"""
        mock_app.config = {'GROK_API_URL': 'https://test.api.com'}
        
        with patch.dict(os.environ, {}, clear=True):
            with pytest.raises(ValueError, match="XAI_API_KEY is not set"):
                validate_environment()
    
    @patch('app.services.langchain_base.current_app')
    @patch('app.services.langchain_base.XAILLM')
    def test_connection_test_success(self, mock_llm_class, mock_app):
        """Test successful connection test"""
        mock_app.config = {
            'XAI_API_KEY': 'test-key',
            'GROK_API_URL': 'https://test.api.com'
        }
        
        mock_llm = Mock()
        mock_llm._call.return_value = "Hello, this is a test"
        mock_llm_class.return_value = mock_llm
        
        success, response = test_xai_connection()
        
        assert success is True
        assert response == "Hello, this is a test"
    
    @patch('app.services.langchain_base.current_app')
    @patch('app.services.langchain_base.XAILLM')
    def test_connection_test_failure(self, mock_llm_class, mock_app):
        """Test connection test failure"""
        mock_app.config = {
            'XAI_API_KEY': 'test-key',
            'GROK_API_URL': 'https://test.api.com'
        }
        
        mock_llm_class.side_effect = Exception("Connection failed")
        
        success, response = test_xai_connection()
        
        assert success is False
        assert "Connection failed" in response

class TestSurveyGenerationChain:
    """Test survey generation chain"""
    
    @patch('app.services.langchain_chains.validate_environment')
    @patch('app.services.langchain_chains.XAILLM')
    def test_survey_generation_success(self, mock_llm_class, mock_validate):
        """Test successful survey generation"""
        mock_validate.return_value = True
        
        # Mock LLM response
        mock_llm = Mock()
        mock_chain = Mock()
        mock_chain.run.return_value = {
            "questions": [
                {
                    "id": 1,
                    "question": "What is Python?",
                    "type": "multiple_choice",
                    "options": ["A language", "A snake", "A tool", "A framework"],
                    "correct_answer": "A language",
                    "difficulty": "beginner",
                    "topic": "basics"
                }
            ],
            "total_questions": 1,
            "subject": "python"
        }
        
        with patch('app.services.langchain_chains.LLMChain', return_value=mock_chain):
            survey_chain = SurveyGenerationChain()
            result = survey_chain.generate_survey("python")
        
        assert result["subject"] == "python"
        assert len(result["questions"]) == 1
        assert result["total_questions"] == 1
    
    @patch('app.services.langchain_chains.validate_environment')
    @patch('app.services.langchain_chains.XAILLM')
    def test_survey_generation_validation_failure(self, mock_llm_class, mock_validate):
        """Test survey generation with validation failure"""
        mock_validate.return_value = True
        
        # Mock LLM response with missing keys
        mock_llm = Mock()
        mock_chain = Mock()
        mock_chain.run.return_value = {
            "questions": [],
            # Missing total_questions and subject
        }
        
        with patch('app.services.langchain_chains.LLMChain', return_value=mock_chain):
            survey_chain = SurveyGenerationChain()
            
            with pytest.raises(ValueError, match="does not have required structure"):
                survey_chain.generate_survey("python")

class TestLangChainPipelineService:
    """Test LangChain pipeline service"""
    
    @patch('app.services.langchain_pipeline.validate_environment')
    @patch('app.services.langchain_pipeline.SurveyGenerationChain')
    def test_pipeline_initialization(self, mock_survey_chain, mock_validate):
        """Test pipeline service initialization"""
        mock_validate.return_value = True
        
        pipeline = LangChainPipelineService()
        
        assert pipeline is not None
        mock_validate.assert_called_once()
    
    @patch('app.services.langchain_pipeline.validate_environment')
    @patch('app.services.langchain_pipeline.test_xai_connection')
    def test_connection_test_success(self, mock_test_connection, mock_validate):
        """Test successful connection test"""
        mock_validate.return_value = True
        mock_test_connection.return_value = (True, "Connection successful")
        
        with patch('app.services.langchain_pipeline.SurveyGenerationChain'):
            pipeline = LangChainPipelineService()
            result = pipeline.test_connection()
        
        assert result["status"] == "success"
        assert result["message"] == "Connection successful"
    
    @patch('app.services.langchain_pipeline.validate_environment')
    def test_pipeline_status(self, mock_validate):
        """Test pipeline status reporting"""
        mock_validate.return_value = True
        
        with patch('app.services.langchain_pipeline.SurveyGenerationChain'):
            pipeline = LangChainPipelineService()
            status = pipeline.get_pipeline_status()
        
        assert status["survey_generation"] == "implemented"
        assert status["curriculum_generation"] == "not_implemented"
        assert status["lesson_planning"] == "not_implemented"
        assert status["content_generation"] == "not_implemented"
        assert status["rag_system"] == "not_implemented"
        assert status["xai_connection"] == "implemented"