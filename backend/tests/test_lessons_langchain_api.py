"""
Tests for LangChain lesson API endpoints
"""
import pytest
import json
from unittest.mock import Mock, patch, MagicMock
from app.api.lessons import lessons_bp
from app.services.pipeline_orchestrator import PipelineStatus, PipelineStage

class TestLessonsLangChainAPI:
    """Test LangChain lesson API endpoints"""
    
    @pytest.fixture
    def client(self, app):
        """Create test client"""
        app.register_blueprint(lessons_bp, url_prefix='/api')
        return app.test_client()
    
    @pytest.fixture
    def mock_survey_data(self):
        """Mock survey data"""
        return {
            'user_id': 'test-user',
            'subject': 'python',
            'skill_level': 'intermediate',
            'answers': [
                {'question_id': 1, 'correct': True, 'topic': 'variables'},
                {'question_id': 2, 'correct': False, 'topic': 'functions'}
            ]
        }
    
    @pytest.fixture
    def mock_curriculum_data(self):
        """Mock curriculum data"""
        return {
            'curriculum': {
                'subject': 'python',
                'skill_level': 'intermediate',
                'total_lessons': 3,
                'learning_objectives': ['Learn Python basics'],
                'topics': [
                    {'lesson_id': 1, 'title': 'Variables and Data Types'},
                    {'lesson_id': 2, 'title': 'Functions and Scope'}
                ]
            },
            'generated_at': '2024-01-15T10:00:00Z',
            'user_id': 'test-user',
            'subject': 'python'
        }
    
    @pytest.fixture
    def mock_lesson_plans_data(self):
        """Mock lesson plans data"""
        return {
            'lesson_plans': [
                {
                    'lesson_id': 1,
                    'title': 'Variables and Data Types',
                    'learning_objectives': ['Understand variables'],
                    'structure': {'introduction': '5 min'}
                }
            ],
            'generated_at': '2024-01-15T10:00:00Z',
            'user_id': 'test-user',
            'subject': 'python'
        }
    
    @pytest.fixture
    def mock_pipeline_progress(self):
        """Mock pipeline progress"""
        return {
            'user_id': 'test-user',
            'subject': 'python',
            'current_stage': 'content_generation',
            'status': 'in_progress',
            'progress_percentage': 75.0,
            'stages_completed': 2,
            'total_stages': 3,
            'current_step': 'Generating lesson content',
            'started_at': '2024-01-15T10:00:00Z'
        }
    
    @patch('app.api.lessons.SubscriptionService')
    @patch('app.api.lessons.UserDataService')
    @patch('app.api.lessons.pipeline_orchestrator')
    def test_generate_lessons_langchain_success(self, mock_orchestrator, mock_user_data, mock_subscription, client, mock_survey_data):
        """Test successful LangChain lesson generation"""
        # Mock subscription check
        mock_subscription.has_active_subscription.return_value = True
        
        # Mock survey data loading
        mock_user_data.load_survey_answers.return_value = mock_survey_data
        
        # Mock pipeline start
        mock_orchestrator.start_full_pipeline.return_value = 'pipeline-123'
        
        response = client.post('/api/users/test-user/subjects/python/lessons/generate-langchain')
        
        assert response.status_code == 202
        data = json.loads(response.data)
        
        assert data['success'] == True
        assert data['pipeline_id'] == 'pipeline-123'
        assert data['generation_method'] == 'langchain'
        assert data['status'] == 'started'
        assert data['details']['user_id'] == 'test-user'
        assert data['details']['subject'] == 'python'
        
        # Verify service calls
        mock_subscription.has_active_subscription.assert_called_once_with('test-user', 'python')
        mock_user_data.load_survey_answers.assert_called_once_with('test-user', 'python')
        mock_orchestrator.start_full_pipeline.assert_called_once()
    
    @patch('app.api.lessons.SubscriptionService')
    @patch('app.api.lessons.UserDataService')
    def test_generate_lessons_langchain_no_subscription(self, mock_user_data, mock_subscription, client):
        """Test LangChain lesson generation without subscription"""
        # Mock subscription check
        mock_subscription.has_active_subscription.return_value = False
        
        response = client.post('/api/users/test-user/subjects/python/lessons/generate-langchain')
        
        assert response.status_code == 403
        data = json.loads(response.data)
        
        assert data['success'] == False
        assert data['error'] == 'subscription_required'
        assert 'Active subscription required' in data['message']
    
    @patch('app.api.lessons.SubscriptionService')
    @patch('app.api.lessons.UserDataService')
    def test_generate_lessons_langchain_no_survey(self, mock_user_data, mock_subscription, client):
        """Test LangChain lesson generation without survey data"""
        # Mock subscription check
        mock_subscription.has_active_subscription.return_value = True
        
        # Mock no survey data
        mock_user_data.load_survey_answers.return_value = None
        
        response = client.post('/api/users/test-user/subjects/python/lessons/generate-langchain')
        
        assert response.status_code == 404
        data = json.loads(response.data)
        
        assert data['success'] == False
        assert data['error'] == 'prerequisite_missing'
        assert 'Survey results not found' in data['message']
    
    @patch('app.api.lessons.pipeline_orchestrator')
    def test_get_pipeline_status_success(self, mock_orchestrator, client, mock_pipeline_progress):
        """Test successful pipeline status retrieval"""
        mock_orchestrator.get_pipeline_progress.return_value = mock_pipeline_progress
        
        response = client.get('/api/users/test-user/subjects/python/lessons/pipeline-status/pipeline-123')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        
        assert data['success'] == True
        assert data['pipeline_id'] == 'pipeline-123'
        assert data['pipeline_status']['user_id'] == 'test-user'
        assert data['pipeline_status']['subject'] == 'python'
        assert data['pipeline_status']['status'] == 'in_progress'
        assert data['pipeline_status']['progress_percentage'] == 75.0
    
    @patch('app.api.lessons.pipeline_orchestrator')
    def test_get_pipeline_status_not_found(self, mock_orchestrator, client):
        """Test pipeline status retrieval for non-existent pipeline"""
        mock_orchestrator.get_pipeline_progress.return_value = None
        
        response = client.get('/api/users/test-user/subjects/python/lessons/pipeline-status/non-existent')
        
        assert response.status_code == 404
        data = json.loads(response.data)
        
        assert data['success'] == False
        assert data['error'] == 'not_found'
        assert data['pipeline_id'] == 'non-existent'
    
    @patch('app.api.lessons.pipeline_orchestrator')
    def test_get_pipeline_status_access_denied(self, mock_orchestrator, client):
        """Test pipeline status retrieval with wrong user"""
        # Mock progress for different user
        wrong_user_progress = {
            'user_id': 'other-user',
            'subject': 'python',
            'status': 'in_progress'
        }
        mock_orchestrator.get_pipeline_progress.return_value = wrong_user_progress
        
        response = client.get('/api/users/test-user/subjects/python/lessons/pipeline-status/pipeline-123')
        
        assert response.status_code == 403
        data = json.loads(response.data)
        
        assert data['success'] == False
        assert data['error'] == 'access_denied'
    
    @patch('app.api.lessons.UserDataService')
    def test_get_curriculum_scheme_success(self, mock_user_data, client, mock_curriculum_data):
        """Test successful curriculum scheme retrieval"""
        mock_user_data.load_curriculum_scheme.return_value = mock_curriculum_data
        
        response = client.get('/api/users/test-user/subjects/python/curriculum')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        
        assert data['success'] == True
        assert data['curriculum']['curriculum']['subject'] == 'python'
        assert data['curriculum']['curriculum']['skill_level'] == 'intermediate'
        assert len(data['curriculum']['curriculum']['topics']) == 2
    
    @patch('app.api.lessons.UserDataService')
    def test_get_curriculum_scheme_not_found(self, mock_user_data, client):
        """Test curriculum scheme retrieval when not found"""
        mock_user_data.load_curriculum_scheme.return_value = None
        
        response = client.get('/api/users/test-user/subjects/python/curriculum')
        
        assert response.status_code == 404
        data = json.loads(response.data)
        
        assert data['success'] == False
        assert data['error'] == 'not_found'
        assert 'Curriculum scheme not found' in data['message']
    
    @patch('app.api.lessons.UserDataService')
    def test_get_lesson_plans_success(self, mock_user_data, client, mock_lesson_plans_data):
        """Test successful lesson plans retrieval"""
        mock_user_data.load_lesson_plans.return_value = mock_lesson_plans_data
        
        response = client.get('/api/users/test-user/subjects/python/lesson-plans')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        
        assert data['success'] == True
        assert len(data['lesson_plans']['lesson_plans']) == 1
        assert data['lesson_plans']['lesson_plans'][0]['lesson_id'] == 1
        assert data['lesson_plans']['lesson_plans'][0]['title'] == 'Variables and Data Types'
    
    @patch('app.api.lessons.UserDataService')
    def test_get_lesson_plans_not_found(self, mock_user_data, client):
        """Test lesson plans retrieval when not found"""
        mock_user_data.load_lesson_plans.return_value = None
        
        response = client.get('/api/users/test-user/subjects/python/lesson-plans')
        
        assert response.status_code == 404
        data = json.loads(response.data)
        
        assert data['success'] == False
        assert data['error'] == 'not_found'
        assert 'Lesson plans not found' in data['message']
    
    @patch('app.api.lessons.SubscriptionService')
    @patch('app.api.lessons.UserDataService')
    def test_get_langchain_lesson_success(self, mock_user_data, mock_subscription, client):
        """Test successful LangChain lesson retrieval"""
        # Mock subscription check
        mock_subscription.has_active_subscription.return_value = True
        
        # Mock lesson content with metadata
        lesson_content = """---
user_id: test-user
subject: python
lesson_id: 1
generated_at: 2024-01-15T10:00:00Z
generation_method: langchain
---

# Lesson 1: Variables and Data Types

This lesson covers Python variables and data types.

## Introduction

Variables are containers for storing data values.

## Examples

```python
name = "Alice"
age = 30
```

## Exercises

1. Create a variable to store your name
2. Create a variable to store your age
"""
        
        mock_user_data.load_lesson_content.return_value = lesson_content
        
        response = client.get('/api/users/test-user/subjects/python/lessons/1/langchain')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        
        assert data['success'] == True
        assert data['lesson']['lesson_id'] == 1
        assert data['lesson']['user_id'] == 'test-user'
        assert data['lesson']['subject'] == 'python'
        assert data['lesson']['generation_method'] == 'langchain'
        assert 'Variables and Data Types' in data['lesson']['content']
        assert data['lesson']['metadata']['user_id'] == 'test-user'
        assert data['lesson']['metadata']['lesson_id'] == '1'
    
    @patch('app.api.lessons.SubscriptionService')
    @patch('app.api.lessons.UserDataService')
    def test_get_langchain_lesson_not_found(self, mock_user_data, mock_subscription, client):
        """Test LangChain lesson retrieval when not found"""
        # Mock subscription check
        mock_subscription.has_active_subscription.return_value = True
        
        # Mock no lesson content
        mock_user_data.load_lesson_content.return_value = None
        
        response = client.get('/api/users/test-user/subjects/python/lessons/1/langchain')
        
        assert response.status_code == 404
        data = json.loads(response.data)
        
        assert data['success'] == False
        assert data['error'] == 'not_found'
        assert data['details']['lesson_id'] == 1
    
    @patch('app.api.lessons.pipeline_orchestrator')
    def test_cancel_pipeline_success(self, mock_orchestrator, client, mock_pipeline_progress):
        """Test successful pipeline cancellation"""
        # Mock pipeline progress
        mock_orchestrator.get_pipeline_progress.return_value = mock_pipeline_progress
        mock_orchestrator.cancel_pipeline.return_value = True
        
        response = client.post('/api/users/test-user/subjects/python/lessons/pipeline-cancel/pipeline-123')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        
        assert data['success'] == True
        assert data['pipeline_id'] == 'pipeline-123'
        assert data['status'] == 'cancelled'
        
        # Verify service calls
        mock_orchestrator.get_pipeline_progress.assert_called_once_with('pipeline-123')
        mock_orchestrator.cancel_pipeline.assert_called_once_with('pipeline-123')
    
    @patch('app.api.lessons.pipeline_orchestrator')
    def test_cancel_pipeline_not_found(self, mock_orchestrator, client):
        """Test pipeline cancellation for non-existent pipeline"""
        mock_orchestrator.get_pipeline_progress.return_value = None
        
        response = client.post('/api/users/test-user/subjects/python/lessons/pipeline-cancel/non-existent')
        
        assert response.status_code == 404
        data = json.loads(response.data)
        
        assert data['success'] == False
        assert data['error'] == 'not_found'
        assert data['pipeline_id'] == 'non-existent'
    
    @patch('app.api.lessons.pipeline_orchestrator')
    def test_cancel_pipeline_access_denied(self, mock_orchestrator, client):
        """Test pipeline cancellation with wrong user"""
        # Mock progress for different user
        wrong_user_progress = {
            'user_id': 'other-user',
            'subject': 'python',
            'status': 'in_progress'
        }
        mock_orchestrator.get_pipeline_progress.return_value = wrong_user_progress
        
        response = client.post('/api/users/test-user/subjects/python/lessons/pipeline-cancel/pipeline-123')
        
        assert response.status_code == 403
        data = json.loads(response.data)
        
        assert data['success'] == False
        assert data['error'] == 'access_denied'
    
    @patch('app.api.lessons.pipeline_orchestrator')
    def test_cancel_pipeline_failed(self, mock_orchestrator, client, mock_pipeline_progress):
        """Test pipeline cancellation failure"""
        # Mock pipeline progress
        mock_orchestrator.get_pipeline_progress.return_value = mock_pipeline_progress
        mock_orchestrator.cancel_pipeline.return_value = False
        
        response = client.post('/api/users/test-user/subjects/python/lessons/pipeline-cancel/pipeline-123')
        
        assert response.status_code == 400
        data = json.loads(response.data)
        
        assert data['success'] == False
        assert data['error'] == 'cancellation_failed'
        assert data['pipeline_id'] == 'pipeline-123'
    
    def test_invalid_user_id_validation(self, client):
        """Test validation of invalid user ID"""
        response = client.post('/api/users/invalid..user/subjects/python/lessons/generate-langchain')
        
        assert response.status_code == 400
        data = json.loads(response.data)
        
        assert data['success'] == False
        assert data['error'] == 'validation_error'
        assert 'Invalid user ID format' in data['message']
    
    def test_invalid_subject_validation(self, client):
        """Test validation of invalid subject"""
        response = client.post('/api/users/test-user/subjects/invalid..subject/lessons/generate-langchain')
        
        assert response.status_code == 400
        data = json.loads(response.data)
        
        assert data['success'] == False
        assert data['error'] == 'validation_error'
        assert 'Invalid subject format' in data['message']