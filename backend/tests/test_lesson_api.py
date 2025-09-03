"""
Tests for lesson API endpoints
"""

import pytest
import json
import tempfile
import shutil
from pathlib import Path
from unittest.mock import patch, MagicMock

from app import create_app
from app.services.file_service import FileService


class TestLessonAPI:
    
    def setup_method(self):
        """Set up test environment"""
        # Create test app
        self.app = create_app()
        self.app.config['TESTING'] = True
        self.client = self.app.test_client()
        
        # Test data
        self.test_user_id = "test_user_123"
        self.test_subject = "python"
        
        # Create temporary directory for testing
        self.temp_dir = tempfile.mkdtemp()
        self.original_base_dir = FileService.BASE_DIR
        FileService.BASE_DIR = Path(self.temp_dir) / "users"
        
        # Mock lesson generation result
        self.mock_generation_result = {
            'lessons': [
                {
                    'lesson_number': 1,
                    'title': 'Variables and Data Types',
                    'estimated_time': '30 minutes',
                    'difficulty': 'beginner',
                    'topics': ['variables', 'data_types'],
                    'prerequisites': [],
                    'content': self._get_sample_lesson_content(),
                    'generated_at': '2024-01-01T00:00:00Z'
                },
                {
                    'lesson_number': 2,
                    'title': 'Functions in Python',
                    'estimated_time': '40 minutes',
                    'difficulty': 'beginner',
                    'topics': ['functions', 'parameters'],
                    'prerequisites': ['variables'],
                    'content': self._get_sample_lesson_content(),
                    'generated_at': '2024-01-01T00:00:00Z'
                }
            ],
            'metadata': {
                'user_id': self.test_user_id,
                'subject': self.test_subject,
                'skill_level': 'beginner',
                'total_lessons': 2,
                'generated_at': '2024-01-01T00:00:00Z',
                'topic_analysis': {
                    'strengths': ['variables'],
                    'weaknesses': ['functions']
                },
                'lessons': [
                    {
                        'lesson_number': 1,
                        'title': 'Variables and Data Types',
                        'estimated_time': '30 minutes',
                        'topics': ['variables', 'data_types'],
                        'difficulty': 'beginner'
                    },
                    {
                        'lesson_number': 2,
                        'title': 'Functions in Python',
                        'estimated_time': '40 minutes',
                        'topics': ['functions', 'parameters'],
                        'difficulty': 'beginner'
                    }
                ]
            }
        }
    
    def teardown_method(self):
        """Clean up test environment"""
        FileService.BASE_DIR = self.original_base_dir
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def _get_sample_lesson_content(self):
        """Get sample lesson content for testing"""
        return """# Sample Lesson

## Introduction
This is a sample lesson for testing purposes.

## What You'll Learn
- Basic concepts
- Practical examples

## Content Section

Here's some content with code examples:

```python
# Sample code
def hello_world():
    print("Hello, World!")
```

## Quiz

1. What is the output of the code above?
   a) Hello, World!
   b) Error

**Answer: a**

## Summary

In this lesson, you learned basic concepts.
"""
    
    @patch('app.api.lessons.LessonGenerationService.generate_personalized_lessons')
    @patch('app.api.lessons.LessonFileService.save_lessons')
    def test_generate_lessons_success(self, mock_save_lessons, mock_generate_lessons):
        """Test successful lesson generation"""
        # Mock dependencies
        mock_generate_lessons.return_value = self.mock_generation_result
        mock_save_lessons.return_value = {
            'user_id': self.test_user_id,
            'subject': self.test_subject,
            'saved_successfully': 2,
            'failed_saves': 0,
            'saved_files': [
                {'lesson_number': 1, 'file_path': 'lesson_1.md', 'title': 'Variables and Data Types'},
                {'lesson_number': 2, 'file_path': 'lesson_2.md', 'title': 'Functions in Python'}
            ],
            'failed_files': []
        }
        
        # Make request
        response = self.client.post(f'/api/users/{self.test_user_id}/subjects/{self.test_subject}/lessons/generate')
        
        # Verify response
        assert response.status_code == 201
        data = json.loads(response.data)
        assert data['success'] is True
        assert 'generation_summary' in data
        assert 'save_summary' in data
        assert data['generation_summary']['skill_level'] == 'beginner'
        assert data['generation_summary']['total_lessons'] == 2
        assert data['save_summary']['saved_successfully'] == 2
        
        # Verify service calls
        mock_generate_lessons.assert_called_once_with(self.test_user_id, self.test_subject)
        mock_save_lessons.assert_called_once()
    
    def test_generate_lessons_invalid_user_id(self):
        """Test lesson generation with invalid user ID"""
        invalid_user_id = "invalid user id!"
        
        response = self.client.post(f'/api/users/{invalid_user_id}/subjects/{self.test_subject}/lessons/generate')
        
        assert response.status_code == 400
        data = json.loads(response.data)
        assert data['success'] is False
        assert data['error'] == 'validation_error'
        assert 'invalid user id' in data['message'].lower()
    
    def test_generate_lessons_invalid_subject(self):
        """Test lesson generation with invalid subject"""
        invalid_subject = "Invalid Subject!"
        
        response = self.client.post(f'/api/users/{self.test_user_id}/subjects/{invalid_subject}/lessons/generate')
        
        assert response.status_code == 400
        data = json.loads(response.data)
        assert data['success'] is False
        assert data['error'] == 'validation_error'
        assert 'invalid subject' in data['message'].lower()
    
    @patch('app.api.lessons.LessonGenerationService.generate_personalized_lessons')
    def test_generate_lessons_no_survey_results(self, mock_generate_lessons):
        """Test lesson generation when survey results are missing"""
        mock_generate_lessons.side_effect = FileNotFoundError("Survey results not found")
        
        response = self.client.post(f'/api/users/{self.test_user_id}/subjects/{self.test_subject}/lessons/generate')
        
        assert response.status_code == 404
        data = json.loads(response.data)
        assert data['success'] is False
        assert data['error'] == 'prerequisite_missing'
        assert 'survey' in data['message'].lower()
        assert data['details']['required_action'] == 'complete_survey'
    
    @patch('app.api.lessons.LessonFileService.list_lessons')
    def test_list_lessons_success(self, mock_list_lessons):
        """Test successful lesson listing"""
        mock_list_lessons.return_value = {
            'user_id': self.test_user_id,
            'subject': self.test_subject,
            'total_lessons': 2,
            'skill_level': 'beginner',
            'generated_at': '2024-01-01T00:00:00Z',
            'lessons': [
                {
                    'lesson_number': 1,
                    'title': 'Variables and Data Types',
                    'estimated_time': '30 minutes',
                    'topics': ['variables', 'data_types'],
                    'difficulty': 'beginner',
                    'file_exists': True
                },
                {
                    'lesson_number': 2,
                    'title': 'Functions in Python',
                    'estimated_time': '40 minutes',
                    'topics': ['functions', 'parameters'],
                    'difficulty': 'beginner',
                    'file_exists': True
                }
            ]
        }
        
        response = self.client.get(f'/api/users/{self.test_user_id}/subjects/{self.test_subject}/lessons')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True
        assert len(data['lessons']) == 2
        assert data['summary']['total_lessons'] == 2
        assert data['summary']['skill_level'] == 'beginner'
        
        mock_has_subscription.assert_called_once_with(self.test_user_id, self.test_subject)
        mock_list_lessons.assert_called_once_with(self.test_user_id, self.test_subject)
    
    @patch('app.api.lessons.SubscriptionService.has_active_subscription')
    def test_list_lessons_no_subscription(self, mock_has_subscription):
        """Test lesson listing without subscription"""
        mock_has_subscription.return_value = False
        
        response = self.client.get(f'/api/users/{self.test_user_id}/subjects/{self.test_subject}/lessons')
        
        assert response.status_code == 403
        data = json.loads(response.data)
        assert data['success'] is False
        assert data['error'] == 'subscription_required'
    
    @patch('app.api.lessons.SubscriptionService.has_active_subscription')
    @patch('app.api.lessons.LessonFileService.get_lesson')
    def test_get_lesson_success(self, mock_get_lesson, mock_has_subscription):
        """Test successful lesson retrieval"""
        mock_has_subscription.return_value = True
        mock_get_lesson.return_value = {
            'lesson_number': 1,
            'title': 'Variables and Data Types',
            'estimated_time': '30 minutes',
            'difficulty': 'beginner',
            'topics': ['variables', 'data_types'],
            'content': self._get_sample_lesson_content(),
            'loaded_at': '2024-01-01T00:00:00Z'
        }
        
        response = self.client.get(f'/api/users/{self.test_user_id}/subjects/{self.test_subject}/lessons/1')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True
        assert data['lesson']['lesson_number'] == 1
        assert data['lesson']['title'] == 'Variables and Data Types'
        assert 'content' in data['lesson']
        assert len(data['lesson']['content']) > 0
        
        mock_has_subscription.assert_called_once_with(self.test_user_id, self.test_subject)
        mock_get_lesson.assert_called_once_with(self.test_user_id, self.test_subject, 1)
    
    @patch('app.api.lessons.SubscriptionService.has_active_subscription')
    def test_get_lesson_no_subscription(self, mock_has_subscription):
        """Test lesson retrieval without subscription"""
        mock_has_subscription.return_value = False
        
        response = self.client.get(f'/api/users/{self.test_user_id}/subjects/{self.test_subject}/lessons/1')
        
        assert response.status_code == 403
        data = json.loads(response.data)
        assert data['success'] is False
        assert data['error'] == 'subscription_required'
        assert data['details']['lesson_number'] == 1
    
    @patch('app.api.lessons.SubscriptionService.has_active_subscription')
    @patch('app.api.lessons.LessonFileService.get_lesson')
    def test_get_lesson_not_found(self, mock_get_lesson, mock_has_subscription):
        """Test lesson retrieval when lesson doesn't exist"""
        mock_has_subscription.return_value = True
        mock_get_lesson.side_effect = FileNotFoundError("Lesson not found")
        
        response = self.client.get(f'/api/users/{self.test_user_id}/subjects/{self.test_subject}/lessons/1')
        
        assert response.status_code == 404
        data = json.loads(response.data)
        assert data['success'] is False
        assert data['error'] == 'not_found'
        assert data['details']['lesson_number'] == 1
    
    def test_get_lesson_invalid_lesson_number(self):
        """Test lesson retrieval with invalid lesson number"""
        # Test with non-integer lesson number
        response = self.client.get(f'/api/users/{self.test_user_id}/subjects/{self.test_subject}/lessons/invalid')
        
        assert response.status_code == 404  # Flask returns 404 for invalid route parameters
    
    @patch('app.api.lessons.LessonFileService.delete_lessons')
    def test_delete_lessons_success(self, mock_delete_lessons):
        """Test successful lesson deletion"""
        mock_delete_lessons.return_value = {
            'user_id': self.test_user_id,
            'subject': self.test_subject,
            'total_deleted': 3,
            'deleted_files': ['lesson_1.md', 'lesson_2.md', 'lesson_metadata.json'],
            'deleted_at': '2024-01-01T00:00:00Z'
        }
        
        response = self.client.delete(f'/api/users/{self.test_user_id}/subjects/{self.test_subject}/lessons')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True
        assert data['deletion_summary']['total_deleted'] == 3
        assert len(data['deletion_summary']['deleted_files']) == 3
        
        mock_delete_lessons.assert_called_once_with(self.test_user_id, self.test_subject)
    
    @patch('app.api.lessons.LessonFileService.list_lessons')
    def test_get_lesson_progress_success(self, mock_list_lessons):
        """Test successful lesson progress retrieval"""
        mock_list_lessons.return_value = {
            'user_id': self.test_user_id,
            'subject': self.test_subject,
            'total_lessons': 2,
            'skill_level': 'beginner',
            'generated_at': '2024-01-01T00:00:00Z',
            'lessons': [
                {
                    'lesson_number': 1,
                    'title': 'Variables and Data Types',
                    'estimated_time': '30 minutes',
                    'difficulty': 'beginner',
                    'file_exists': True
                },
                {
                    'lesson_number': 2,
                    'title': 'Functions in Python',
                    'estimated_time': '40 minutes',
                    'difficulty': 'beginner',
                    'file_exists': False
                }
            ]
        }
        
        response = self.client.get(f'/api/users/{self.test_user_id}/subjects/{self.test_subject}/lessons/progress')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True
        assert data['progress']['total_lessons_generated'] == 2
        assert data['progress']['available_lessons'] == 1
        assert data['progress']['progress_percentage'] == 10.0  # 1/10 * 100
        assert len(data['progress']['lessons']) == 2
        assert data['progress']['lessons'][0]['available'] is True
        assert data['progress']['lessons'][1]['available'] is False
        
        mock_list_lessons.assert_called_once_with(self.test_user_id, self.test_subject)
    
    def test_get_lesson_progress_invalid_user_id(self):
        """Test lesson progress with invalid user ID"""
        invalid_user_id = "invalid user id!"
        
        response = self.client.get(f'/api/users/{invalid_user_id}/subjects/{self.test_subject}/lessons/progress')
        
        assert response.status_code == 400
        data = json.loads(response.data)
        assert data['success'] is False
        assert data['error'] == 'validation_error'
    
    @patch('app.api.lessons.SubscriptionService.has_active_subscription')
    @patch('app.api.lessons.LessonGenerationService.generate_personalized_lessons')
    def test_generate_lessons_service_error(self, mock_generate_lessons, mock_has_subscription):
        """Test lesson generation with service error"""
        mock_has_subscription.return_value = True
        mock_generate_lessons.side_effect = Exception("Service error")
        
        response = self.client.post(f'/api/users/{self.test_user_id}/subjects/{self.test_subject}/lessons/generate')
        
        assert response.status_code == 500
        data = json.loads(response.data)
        assert data['success'] is False
        assert data['error'] == 'generation_error'
    
    @patch('app.api.lessons.SubscriptionService.has_active_subscription')
    @patch('app.api.lessons.LessonFileService.list_lessons')
    def test_list_lessons_service_error(self, mock_list_lessons, mock_has_subscription):
        """Test lesson listing with service error"""
        mock_has_subscription.return_value = True
        mock_list_lessons.side_effect = Exception("Service error")
        
        response = self.client.get(f'/api/users/{self.test_user_id}/subjects/{self.test_subject}/lessons')
        
        assert response.status_code == 500
        data = json.loads(response.data)
        assert data['success'] is False
        assert data['error'] == 'retrieval_error'
    
    @patch('app.api.lessons.SubscriptionService.has_active_subscription')
    @patch('app.api.lessons.LessonFileService.get_lesson')
    def test_get_lesson_service_error(self, mock_get_lesson, mock_has_subscription):
        """Test lesson retrieval with service error"""
        mock_has_subscription.return_value = True
        mock_get_lesson.side_effect = Exception("Service error")
        
        response = self.client.get(f'/api/users/{self.test_user_id}/subjects/{self.test_subject}/lessons/1')
        
        assert response.status_code == 500
        data = json.loads(response.data)
        assert data['success'] is False
        assert data['error'] == 'retrieval_error'
    
    @patch('app.api.lessons.LessonFileService.delete_lessons')
    def test_delete_lessons_service_error(self, mock_delete_lessons):
        """Test lesson deletion with service error"""
        mock_delete_lessons.side_effect = Exception("Service error")
        
        response = self.client.delete(f'/api/users/{self.test_user_id}/subjects/{self.test_subject}/lessons')
        
        assert response.status_code == 500
        data = json.loads(response.data)
        assert data['success'] is False
        assert data['error'] == 'deletion_error'
    
    @patch('app.api.lessons.SubscriptionService.has_active_subscription')
    def test_subscription_check_graceful_degradation(self, mock_has_subscription):
        """Test that API continues to work when subscription check fails"""
        mock_has_subscription.side_effect = Exception("Subscription service error")
        
        # The API should continue to work even if subscription check fails
        with patch('app.api.lessons.LessonFileService.list_lessons') as mock_list_lessons:
            mock_list_lessons.return_value = {
                'user_id': self.test_user_id,
                'subject': self.test_subject,
                'total_lessons': 0,
                'lessons': []
            }
            
            response = self.client.get(f'/api/users/{self.test_user_id}/subjects/{self.test_subject}/lessons')
            
            # Should still work despite subscription check failure
            assert response.status_code == 200
            data = json.loads(response.data)
            assert data['success'] is True
    
    def test_api_endpoints_exist(self):
        """Test that all expected API endpoints exist"""
        # Test that endpoints return some response (not 404)
        endpoints = [
            ('POST', f'/api/users/{self.test_user_id}/subjects/{self.test_subject}/lessons/generate'),
            ('GET', f'/api/users/{self.test_user_id}/subjects/{self.test_subject}/lessons'),
            ('GET', f'/api/users/{self.test_user_id}/subjects/{self.test_subject}/lessons/1'),
            ('DELETE', f'/api/users/{self.test_user_id}/subjects/{self.test_subject}/lessons'),
            ('GET', f'/api/users/{self.test_user_id}/subjects/{self.test_subject}/lessons/progress')
        ]
        
        for method, endpoint in endpoints:
            if method == 'POST':
                response = self.client.post(endpoint)
            elif method == 'GET':
                response = self.client.get(endpoint)
            elif method == 'DELETE':
                response = self.client.delete(endpoint)
            
            # Should not return 404 (endpoint exists)
            assert response.status_code != 404