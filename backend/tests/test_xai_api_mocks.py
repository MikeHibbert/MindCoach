"""
Mock tests for xAI API interactions
"""
import pytest
import json
import requests
from unittest.mock import Mock, patch, MagicMock
from app.services.langchain_base import (
    XAILLM,
    XAIAPIError,
    XAILLMConfig,
    test_xai_connection
)

class TestXAIAPIMocks:
    """Mock tests for xAI API interactions"""
    
    @pytest.fixture
    def mock_api_response_success(self):
        """Mock successful API response"""
        return {
            "choices": [
                {
                    "message": {
                        "content": "This is a test response from Grok-3 Mini"
                    }
                }
            ],
            "usage": {
                "prompt_tokens": 10,
                "completion_tokens": 15,
                "total_tokens": 25
            }
        }
    
    @pytest.fixture
    def mock_api_response_json(self):
        """Mock API response with JSON content"""
        return {
            "choices": [
                {
                    "message": {
                        "content": '{"questions": [{"id": 1, "question": "Test?"}], "total_questions": 1}'
                    }
                }
            ]
        }
    
    @patch('app.services.langchain_base.current_app')
    @patch('app.services.langchain_base.requests.post')
    def test_successful_api_call_mock(self, mock_post, mock_app, mock_api_response_success):
        """Test successful API call with mocked response"""
        mock_app.config = {'XAI_API_KEY': 'test-key', 'GROK_API_URL': 'https://test.api.com'}
        
        # Mock successful HTTP response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = mock_api_response_success
        mock_post.return_value = mock_response
        
        llm = XAILLM()
        result = llm._call("Test prompt")
        
        assert result == "This is a test response from Grok-3 Mini"
        
        # Verify API call was made correctly
        mock_post.assert_called_once()
        call_args = mock_post.call_args
        
        # Check URL
        assert call_args[0][0] == "https://test.api.com/chat/completions"
        
        # Check headers
        headers = call_args[1]['headers']
        assert headers['Authorization'] == 'Bearer test-key'
        assert headers['Content-Type'] == 'application/json'
        
        # Check payload
        payload = call_args[1]['json']
        assert payload['model'] == 'grok-3-mini'
        assert payload['messages'][0]['content'] == 'Test prompt'
        assert payload['temperature'] == 0.7
        assert payload['max_tokens'] == 2000
    
    @patch('app.services.langchain_base.current_app')
    @patch('app.services.langchain_base.requests.post')
    def test_rate_limit_handling_mock(self, mock_post, mock_app):
        """Test rate limit handling with mocked responses"""
        mock_app.config = {'XAI_API_KEY': 'test-key'}
        
        # Mock rate limit response followed by success
        rate_limit_response = Mock()
        rate_limit_response.status_code = 429
        rate_limit_response.text = "Rate limit exceeded"
        
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
    def test_server_error_retry_mock(self, mock_post, mock_app):
        """Test server error retry logic with mocked responses"""
        mock_app.config = {'XAI_API_KEY': 'test-key'}
        
        # Mock server error responses followed by success
        server_error_response = Mock()
        server_error_response.status_code = 500
        server_error_response.text = "Internal server error"
        
        success_response = Mock()
        success_response.status_code = 200
        success_response.json.return_value = {
            "choices": [{"message": {"content": "Success after server recovery"}}]
        }
        
        mock_post.side_effect = [
            server_error_response,
            server_error_response,
            success_response
        ]
        
        llm = XAILLM()
        
        with patch('time.sleep'):  # Mock sleep to speed up test
            result = llm._call("Test prompt")
        
        assert result == "Success after server recovery"
        assert mock_post.call_count == 3
    
    @patch('app.services.langchain_base.current_app')
    @patch('app.services.langchain_base.requests.post')
    def test_client_error_no_retry_mock(self, mock_post, mock_app):
        """Test that client errors don't trigger retries"""
        mock_app.config = {'XAI_API_KEY': 'test-key'}
        
        # Mock client error response (400 Bad Request)
        client_error_response = Mock()
        client_error_response.status_code = 400
        client_error_response.text = "Bad request - invalid parameters"
        mock_post.return_value = client_error_response
        
        llm = XAILLM()
        
        with pytest.raises(XAIAPIError, match="API error 400"):
            llm._call("Invalid prompt")
        
        # Should only be called once (no retries for client errors)
        assert mock_post.call_count == 1
    
    @patch('app.services.langchain_base.current_app')
    @patch('app.services.langchain_base.requests.post')
    def test_timeout_retry_mock(self, mock_post, mock_app):
        """Test timeout handling with mocked responses"""
        mock_app.config = {'XAI_API_KEY': 'test-key'}
        
        # Mock timeout followed by success
        success_response = Mock()
        success_response.status_code = 200
        success_response.json.return_value = {
            "choices": [{"message": {"content": "Success after timeout recovery"}}]
        }
        
        mock_post.side_effect = [
            requests.exceptions.Timeout("Request timeout"),
            success_response
        ]
        
        llm = XAILLM()
        
        with patch('time.sleep'):  # Mock sleep to speed up test
            result = llm._call("Test prompt")
        
        assert result == "Success after timeout recovery"
        assert mock_post.call_count == 2
    
    @patch('app.services.langchain_base.current_app')
    @patch('app.services.langchain_base.requests.post')
    def test_connection_error_retry_mock(self, mock_post, mock_app):
        """Test connection error handling with mocked responses"""
        mock_app.config = {'XAI_API_KEY': 'test-key'}
        
        # Mock connection error followed by success
        success_response = Mock()
        success_response.status_code = 200
        success_response.json.return_value = {
            "choices": [{"message": {"content": "Success after connection recovery"}}]
        }
        
        mock_post.side_effect = [
            requests.exceptions.ConnectionError("Connection failed"),
            success_response
        ]
        
        llm = XAILLM()
        
        with patch('time.sleep'):  # Mock sleep to speed up test
            result = llm._call("Test prompt")
        
        assert result == "Success after connection recovery"
        assert mock_post.call_count == 2
    
    @patch('app.services.langchain_base.current_app')
    @patch('app.services.langchain_base.requests.post')
    def test_all_retries_exhausted_mock(self, mock_post, mock_app):
        """Test behavior when all retries are exhausted"""
        mock_app.config = {'XAI_API_KEY': 'test-key'}
        
        # Mock consistent failures
        error_response = Mock()
        error_response.status_code = 500
        error_response.text = "Persistent server error"
        mock_post.return_value = error_response
        
        llm = XAILLM()
        
        with patch('time.sleep'):  # Mock sleep to speed up test
            with pytest.raises(XAIAPIError, match="All 3 retries exhausted"):
                llm._call("Test prompt")
        
        # Should be called max_retries times (3)
        assert mock_post.call_count == 3
    
    @patch('app.services.langchain_base.current_app')
    @patch('app.services.langchain_base.requests.post')
    def test_json_response_parsing_mock(self, mock_post, mock_app, mock_api_response_json):
        """Test JSON response parsing with mocked API response"""
        mock_app.config = {'XAI_API_KEY': 'test-key'}
        
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = mock_api_response_json
        mock_post.return_value = mock_response
        
        llm = XAILLM()
        result = llm._call("Generate a JSON survey")
        
        # Should return the JSON string content
        expected_json = '{"questions": [{"id": 1, "question": "Test?"}], "total_questions": 1}'
        assert result == expected_json
        
        # Verify it's valid JSON
        parsed = json.loads(result)
        assert parsed['total_questions'] == 1
        assert len(parsed['questions']) == 1
    
    @patch('app.services.langchain_base.current_app')
    @patch('app.services.langchain_base.requests.post')
    def test_custom_parameters_mock(self, mock_post, mock_app):
        """Test API call with custom parameters"""
        mock_app.config = {'XAI_API_KEY': 'test-key'}
        
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "choices": [{"message": {"content": "Custom response"}}]
        }
        mock_post.return_value = mock_response
        
        # Create LLM with custom parameters
        llm = XAILLM(temperature=0.3, max_tokens=1000)
        result = llm._call("Test prompt", temperature=0.1, max_tokens=500)
        
        assert result == "Custom response"
        
        # Verify custom parameters were used
        call_args = mock_post.call_args
        payload = call_args[1]['json']
        assert payload['temperature'] == 0.1  # Override parameter
        assert payload['max_tokens'] == 500    # Override parameter
    
    @patch('app.services.langchain_base.current_app')
    @patch('app.services.langchain_base.requests.post')
    def test_stop_sequences_mock(self, mock_post, mock_app):
        """Test API call with stop sequences"""
        mock_app.config = {'XAI_API_KEY': 'test-key'}
        
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "choices": [{"message": {"content": "Response with stop"}}]
        }
        mock_post.return_value = mock_response
        
        llm = XAILLM()
        result = llm._call("Test prompt", stop=["END", "STOP"])
        
        assert result == "Response with stop"
        
        # Verify stop sequences were included
        call_args = mock_post.call_args
        payload = call_args[1]['json']
        assert payload['stop'] == ["END", "STOP"]

class TestXAIConnectionTestMocks:
    """Mock tests for xAI connection testing"""
    
    @patch('app.services.langchain_base.current_app')
    @patch('app.services.langchain_base.XAILLM')
    def test_connection_test_success_mock(self, mock_llm_class, mock_app):
        """Test successful connection test with mocked LLM"""
        mock_app.config = {'XAI_API_KEY': 'test-key', 'GROK_API_URL': 'test-url'}
        
        mock_llm = Mock()
        mock_llm._call.return_value = "Hello, this is a test"
        mock_llm_class.return_value = mock_llm
        
        success, response = test_xai_connection()
        
        assert success == True
        assert response == "Hello, this is a test"
        
        # Verify LLM was created with correct parameters
        mock_llm_class.assert_called_once_with(temperature=0.1, max_tokens=50)
        
        # Verify test call was made
        mock_llm._call.assert_called_once_with("Say 'Hello, this is a test' and nothing else.")
    
    @patch('app.services.langchain_base.current_app')
    @patch('app.services.langchain_base.XAILLM')
    def test_connection_test_failure_mock(self, mock_llm_class, mock_app):
        """Test connection test failure with mocked LLM"""
        mock_app.config = {'XAI_API_KEY': 'test-key', 'GROK_API_URL': 'test-url'}
        
        # Mock LLM creation failure
        mock_llm_class.side_effect = XAIAPIError("Connection failed")
        
        success, response = test_xai_connection()
        
        assert success == False
        assert "Connection failed" in response
    
    @patch('app.services.langchain_base.current_app')
    @patch('app.services.langchain_base.validate_environment')
    def test_connection_test_environment_failure_mock(self, mock_validate, mock_app):
        """Test connection test with environment validation failure"""
        mock_app.config = {}
        mock_validate.side_effect = ValueError("XAI_API_KEY is not set")
        
        success, response = test_xai_connection()
        
        assert success == False
        assert "XAI_API_KEY is not set" in response

class TestXAILLMConfigMocks:
    """Mock tests for XAI LLM configuration"""
    
    def test_config_validation_mock(self):
        """Test configuration validation with mocked values"""
        # Test valid configuration
        config = XAILLMConfig(
            api_key="test-key-123",
            api_url="https://custom.api.com/v1",
            model="grok-3-mini",
            temperature=0.5,
            max_tokens=1500,
            timeout=30,
            max_retries=5,
            retry_delay=2.0
        )
        
        assert config.api_key == "test-key-123"
        assert config.api_url == "https://custom.api.com/v1"
        assert config.model == "grok-3-mini"
        assert config.temperature == 0.5
        assert config.max_tokens == 1500
        assert config.timeout == 30
        assert config.max_retries == 5
        assert config.retry_delay == 2.0
    
    def test_config_defaults_mock(self):
        """Test configuration defaults with minimal input"""
        config = XAILLMConfig(api_key="test-key")
        
        # Verify defaults are applied
        assert config.api_key == "test-key"
        assert config.api_url == "https://api.x.ai/v1"
        assert config.model == "grok-3-mini"
        assert config.temperature == 0.7
        assert config.max_tokens == 2000
        assert config.timeout == 60
        assert config.max_retries == 3
        assert config.retry_delay == 1.0

class TestXAIErrorHandlingMocks:
    """Mock tests for xAI error handling scenarios"""
    
    @patch('app.services.langchain_base.current_app')
    @patch('app.services.langchain_base.requests.post')
    def test_malformed_response_mock(self, mock_post, mock_app):
        """Test handling of malformed API responses"""
        mock_app.config = {'XAI_API_KEY': 'test-key'}
        
        # Mock malformed JSON response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.side_effect = json.JSONDecodeError("Invalid JSON", "", 0)
        mock_response.text = "Invalid JSON response"
        mock_post.return_value = mock_response
        
        llm = XAILLM()
        
        with pytest.raises(Exception):  # Should raise some exception for malformed response
            llm._call("Test prompt")
    
    @patch('app.services.langchain_base.current_app')
    @patch('app.services.langchain_base.requests.post')
    def test_missing_content_field_mock(self, mock_post, mock_app):
        """Test handling of API response missing content field"""
        mock_app.config = {'XAI_API_KEY': 'test-key'}
        
        # Mock response missing content field
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "choices": [
                {
                    "message": {
                        # Missing "content" field
                        "role": "assistant"
                    }
                }
            ]
        }
        mock_post.return_value = mock_response
        
        llm = XAILLM()
        
        with pytest.raises(KeyError):  # Should raise KeyError for missing content
            llm._call("Test prompt")
    
    @patch('app.services.langchain_base.current_app')
    @patch('app.services.langchain_base.requests.post')
    def test_empty_choices_array_mock(self, mock_post, mock_app):
        """Test handling of API response with empty choices array"""
        mock_app.config = {'XAI_API_KEY': 'test-key'}
        
        # Mock response with empty choices
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "choices": [],  # Empty choices array
            "usage": {"total_tokens": 0}
        }
        mock_post.return_value = mock_response
        
        llm = XAILLM()
        
        with pytest.raises(IndexError):  # Should raise IndexError for empty choices
            llm._call("Test prompt")