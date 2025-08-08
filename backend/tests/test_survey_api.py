"""
Integration tests for Survey API endpoints
"""

import pytest
import json
from unittest.mock import patch, MagicMock
from app import create_app


class TestSurveyAPI:
    """Test cases for Survey API endpoints"""
    
    @pytest.fixture
    def app(self):
        """Create test Flask application"""
        app = create_app('testing')
        return app
    
    @pytest.fixture
    def client(self, app):
        """Create test client"""
        return app.test_client()
    
    @pytest.fixture
    def sample_survey(self):
        """Sample survey data for testing"""
        return {
            'subject': 'python',
            'user_id': 'test_user',
            'questions': [
                {
                    'id': 1,
                    'question': 'What is a list?',
                    'type': 'multiple_choice',
                    'options': ['A', 'B', 'C', 'D'],
                    'correct_answer': 0,
                    'difficulty': 'beginner',
                    'topic': 'data_structures'
                },
                {
                    'id': 2,
                    'question': 'What is a decorator?',
                    'type': 'multiple_choice',
                    'options': ['A', 'B', 'C', 'D'],
                    'correct_answer': 1,
                    'difficulty': 'intermediate',
                    'topic': 'decorators'
                }
            ],
            'total_questions': 2,
            'generated_at': '2024-01-15T10:30:00Z'
        }
    
    @pytest.fixture
    def sample_answers(self):
        """Sample survey answers for testing"""
        return [
            {'question_id': 1, 'answer': 0},
            {'question_id': 2, 'answer': 1}
        ]
    
    @pytest.fixture
    def sample_analysis_results(self):
        """Sample analysis results for testing"""
        return {
            'user_id': 'test_user',
            'subject': 'python',
            'skill_level': 'intermediate',
            'accuracy': 1.0,
            'total_questions': 2,
            'correct_answers': 2,
            'topic_analysis': {
                'strengths': ['data_structures', 'decorators'],
                'weaknesses': []
            },
            'recommendations': ['Great job!'],
            'processed_at': '2024-01-15T11:00:00Z'
        }
    
    @patch('app.api.surveys.SurveyGenerationService.generate_survey')
    @patch('app.api.surveys.FileService.save_json')
    def test_generate_survey_success(self, mock_save, mock_generate, client, sample_survey):
        """Test successful survey generation"""
        mock_generate.return_value = sample_survey
        
        response = client.post('/api/users/test_user/subjects/python/survey/generate')
        
        assert response.status_code == 201
        data = json.loads(response.data)
        
        assert data['success'] is True
        assert 'survey' in data
        assert data['survey']['subject'] == 'python'
        assert data['survey']['user_id'] == 'test_user'
        assert len(data['survey']['questions']) == 2
        
        # Verify correct answers are removed from response
        for question in data['survey']['questions']:
            assert 'correct_answer' not in question
        
        # Verify service calls
        mock_generate.assert_called_once_with('python', 'test_user')
        mock_save.assert_called_once()
    
    @patch('app.api.surveys.SurveyAnalysisService.process_survey_answers')
    def test_submit_survey_success(self, mock_process, client, sample_answers, sample_analysis_results):
        """Test successful survey submission"""
        mock_process.return_value = sample_analysis_results
        
        response = client.post(
            '/api/users/test_user/subjects/python/survey/submit',
            data=json.dumps({'answers': sample_answers}),
            content_type='application/json'
        )
        
        assert response.status_code == 200
        data = json.loads(response.data)
        
        assert data['success'] is True
        assert 'results' in data
        assert data['results']['skill_level'] == 'intermediate'
        assert data['results']['accuracy'] == 1.0
        assert data['results']['total_questions'] == 2
        
        mock_process.assert_called_once_with('test_user', 'python', sample_answers)
    
    @patch('app.api.surveys.SurveyAnalysisService.get_survey_results')
    def test_get_survey_results_success(self, mock_get_results, client, sample_analysis_results):
        """Test successful survey results retrieval"""
        mock_get_results.return_value = sample_analysis_results
        
        response = client.get('/api/users/test_user/subjects/python/survey/results')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        
        assert data['success'] is True
        assert 'results' in data
        assert data['results']['skill_level'] == 'intermediate'
        assert data['results']['accuracy'] == 1.0
        
        mock_get_results.assert_called_once_with('test_user', 'python')