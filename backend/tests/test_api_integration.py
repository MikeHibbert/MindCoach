"""
Integration tests for API endpoints
Tests the complete flow from API request to response including database and file operations
"""

import pytest
import json
import tempfile
import shutil
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock

from app import create_app, db
from app.models.user import User
from app.models.subscription import Subscription
from app.models.survey_result import SurveyResult


@pytest.fixture(scope='function')
def app():
    """Create test Flask application"""
    # Create temporary directory for test files
    test_dir = tempfile.mkdtemp()
    
    config = {
        'TESTING': True,
        'SQLALCHEMY_DATABASE_URI': 'sqlite:///:memory:',
        'SQLALCHEMY_TRACK_MODIFICATIONS': False,
        'WTF_CSRF_ENABLED': False,
        'SECRET_KEY': 'test-secret-key'
    }
    
    app = create_app(config)
    
    with app.app_context():
        db.create_all()
        
        # Mock file service base directory
        with patch('app.services.file_service.FileService.BASE_DIR') as mock_base_dir:
            mock_base_dir.return_value = test_dir
            yield app
        
        db.drop_all()
    
    # Cleanup
    shutil.rmtree(test_dir, ignore_errors=True)


@pytest.fixture(scope='function')
def client(app):
    """Create test client"""
    return app.test_client()


@pytest.fixture(scope='function')
def setup_test_data(app):
    """Set up test data for integration tests"""
    with app.app_context():
        # Create test user
        user = User(user_id='integration_user', email='integration@test.com')
        db.session.add(user)
        
        # Create active subscription
        subscription = Subscription(
            user_id='integration_user',
            subject='python',
            status='active',
            expires_at=datetime.utcnow() + timedelta(days=30)
        )
        db.session.add(subscription)
        
        # Create survey result
        survey_result = SurveyResult(
            user_id='integration_user',
            subject='python',
            skill_level='intermediate'
        )
        db.session.add(survey_result)
        
        db.session.commit()
        
        return {
            'user_id': 'integration_user',
            'subject': 'python',
            'skill_level': 'intermediate'
        }


class TestCompleteUserWorkflow:
    """Test complete user workflow from registration to lesson access"""
    
    def test_complete_user_journey(self, client, app):
        """Test complete user journey: create user -> purchase subscription -> take survey -> generate lessons -> access lessons"""
        
        # Step 1: Create user
        user_data = {
            'user_id': 'journey_user',
            'email': 'journey@test.com'
        }
        
        response = client.post('/api/users',
                             data=json.dumps(user_data),
                             content_type='application/json')
        
        assert response.status_code == 201
        data = json.loads(response.data)
        assert data['user']['user_id'] == 'journey_user'
        
        # Step 2: Check subscription status (should be none)
        response = client.get('/api/users/journey_user/subscriptions/python/status')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['has_active_subscription'] == False
        
        # Step 3: Purchase subscription
        response = client.post('/api/users/journey_user/subscriptions/python')
        assert response.status_code == 201
        data = json.loads(response.data)
        assert data['subscription']['status'] == 'active'
        
        # Step 4: Generate survey
        with patch('app.services.survey_generation_service.SurveyGenerationService.generate_survey') as mock_survey:
            mock_survey.return_value = {
                'questions': [
                    {
                        'id': 1,
                        'question': 'What is Python?',
                        'type': 'multiple_choice',
                        'options': ['Language', 'Snake', 'Tool', 'Framework'],
                        'correct_answer': 'Language'
                    }
                ],
                'generated_at': datetime.utcnow().isoformat()
            }
            
            response = client.post('/api/users/journey_user/subjects/python/survey/generate')
            assert response.status_code == 201
            data = json.loads(response.data)
            assert 'survey' in data
            assert len(data['survey']['questions']) == 1
        
        # Step 5: Submit survey answers
        survey_answers = {
            'answers': [
                {'question_id': 1, 'answer': 'Language'}
            ]
        }
        
        with patch('app.services.survey_analysis_service.SurveyAnalysisService.process_survey_answers') as mock_analysis:
            mock_analysis.return_value = {
                'user_id': 'journey_user',
                'subject': 'python',
                'skill_level': 'intermediate',
                'accuracy': 100.0,
                'total_questions': 1,
                'correct_answers': 1,
                'topic_analysis': {'variables': {'accuracy': 100.0}},
                'recommendations': ['Continue with intermediate topics'],
                'processed_at': datetime.utcnow().isoformat()
            }
            
            response = client.post('/api/users/journey_user/subjects/python/survey/submit',
                                 data=json.dumps(survey_answers),
                                 content_type='application/json')
            
            assert response.status_code == 200
            data = json.loads(response.data)
            assert data['results']['skill_level'] == 'intermediate'
        
        # Step 6: Generate lessons
        with patch('app.services.lesson_generation_service.LessonGenerationService.generate_personalized_lessons') as mock_lessons, \
             patch('app.services.lesson_file_service.LessonFileService.save_lessons') as mock_save:
            
            mock_lessons.return_value = {
                'lessons': [
                    {
                        'lesson_number': 1,
                        'title': 'Python Basics',
                        'content': '# Python Basics\nLesson content here...',
                        'estimated_time': '30 minutes',
                        'difficulty': 'intermediate',
                        'topics': ['variables', 'functions']
                    }
                ],
                'metadata': {
                    'skill_level': 'intermediate',
                    'total_lessons': 1,
                    'generated_at': datetime.utcnow().isoformat(),
                    'topic_analysis': {'variables': 'known'}
                }
            }
            
            mock_save.return_value = {
                'saved_successfully': 1,
                'failed_saves': 0,
                'saved_files': ['lesson_1.md'],
                'failed_files': []
            }
            
            response = client.post('/api/users/journey_user/subjects/python/lessons/generate')
            assert response.status_code == 201
            data = json.loads(response.data)
            assert data['generation_summary']['total_lessons'] == 1
            assert data['save_summary']['saved_successfully'] == 1
        
        # Step 7: List lessons
        with patch('app.services.lesson_file_service.LessonFileService.list_lessons') as mock_list:
            mock_list.return_value = {
                'user_id': 'journey_user',
                'subject': 'python',
                'total_lessons': 1,
                'skill_level': 'intermediate',
                'generated_at': datetime.utcnow().isoformat(),
                'lessons': [
                    {
                        'lesson_number': 1,
                        'title': 'Python Basics',
                        'estimated_time': '30 minutes',
                        'difficulty': 'intermediate',
                        'topics': ['variables', 'functions'],
                        'file_exists': True
                    }
                ]
            }
            
            response = client.get('/api/users/journey_user/subjects/python/lessons')
            assert response.status_code == 200
            data = json.loads(response.data)
            assert data['summary']['total_lessons'] == 1
        
        # Step 8: Get specific lesson
        with patch('app.services.lesson_file_service.LessonFileService.get_lesson') as mock_get_lesson:
            mock_get_lesson.return_value = {
                'lesson_number': 1,
                'title': 'Python Basics',
                'content': '# Python Basics\nLesson content here...',
                'estimated_time': '30 minutes',
                'difficulty': 'intermediate',
                'topics': ['variables', 'functions'],
                'loaded_at': datetime.utcnow().isoformat()
            }
            
            response = client.get('/api/users/journey_user/subjects/python/lessons/1')
            assert response.status_code == 200
            data = json.loads(response.data)
            assert data['lesson']['title'] == 'Python Basics'


class TestAPIErrorHandling:
    """Test API error handling and edge cases"""
    
    def test_invalid_user_id_format(self, client):
        """Test API responses to invalid user ID formats"""
        invalid_user_ids = [
            'user with spaces',
            'user@invalid',
            '../../../etc',
            'user/with/slashes',
            'a' * 51  # Too long
        ]
        
        for invalid_id in invalid_user_ids:
            response = client.get(f'/api/users/{invalid_id}')
            assert response.status_code == 400
            data = json.loads(response.data)
            assert 'validation_error' in data['error'] or 'INVALID_USER_ID' in data['error']['code']
    
    def test_invalid_subject_format(self, client, setup_test_data):
        """Test API responses to invalid subject formats"""
        test_data = setup_test_data
        user_id = test_data['user_id']
        
        invalid_subjects = [
            'subject with spaces',
            'subject@invalid',
            '../../../etc',
            'subject/with/slashes',
            'a' * 51  # Too long
        ]
        
        for invalid_subject in invalid_subjects:
            response = client.get(f'/api/users/{user_id}/subjects/{invalid_subject}/lessons')
            assert response.status_code == 400
            data = json.loads(response.data)
            assert 'validation_error' in data['error']
    
    def test_unauthorized_access_without_subscription(self, client, app):
        """Test that users without subscriptions cannot access premium features"""
        # Create user without subscription
        with app.app_context():
            user = User(user_id='no_sub_user', email='nosub@test.com')
            db.session.add(user)
            db.session.commit()
        
        # Try to generate lessons without subscription
        response = client.post('/api/users/no_sub_user/subjects/python/lessons/generate')
        assert response.status_code == 403
        data = json.loads(response.data)
        assert data['error'] == 'subscription_required'
        
        # Try to list lessons without subscription
        response = client.get('/api/users/no_sub_user/subjects/python/lessons')
        assert response.status_code == 403
        data = json.loads(response.data)
        assert data['error'] == 'subscription_required'
        
        # Try to get specific lesson without subscription
        response = client.get('/api/users/no_sub_user/subjects/python/lessons/1')
        assert response.status_code == 403
        data = json.loads(response.data)
        assert data['error'] == 'subscription_required'
    
    def test_expired_subscription_handling(self, client, app):
        """Test handling of expired subscriptions"""
        with app.app_context():
            # Create user with expired subscription
            user = User(user_id='expired_user', email='expired@test.com')
            db.session.add(user)
            
            expired_subscription = Subscription(
                user_id='expired_user',
                subject='python',
                status='active',
                expires_at=datetime.utcnow() - timedelta(days=1)
            )
            db.session.add(expired_subscription)
            db.session.commit()
        
        # Try to access lessons with expired subscription
        response = client.get('/api/users/expired_user/subjects/python/lessons')
        assert response.status_code == 403
        data = json.loads(response.data)
        assert data['error'] == 'subscription_required'
    
    def test_missing_survey_for_lesson_generation(self, client, setup_test_data):
        """Test lesson generation when survey results are missing"""
        test_data = setup_test_data
        user_id = test_data['user_id']
        
        with patch('app.services.lesson_generation_service.LessonGenerationService.generate_personalized_lessons') as mock_lessons:
            mock_lessons.side_effect = FileNotFoundError("Survey results not found")
            
            response = client.post(f'/api/users/{user_id}/subjects/python/lessons/generate')
            assert response.status_code == 404
            data = json.loads(response.data)
            assert data['error'] == 'prerequisite_missing'
            assert 'complete_survey' in data['details']['required_action']
    
    def test_database_connection_failure(self, client, setup_test_data):
        """Test API behavior when database operations fail"""
        test_data = setup_test_data
        user_id = test_data['user_id']
        
        with patch('app.services.subscription_service.SubscriptionService.has_active_subscription') as mock_sub:
            mock_sub.side_effect = Exception("Database connection failed")
            
            # API should continue gracefully when subscription check fails
            with patch('app.services.lesson_file_service.LessonFileService.list_lessons') as mock_list:
                mock_list.return_value = {
                    'user_id': user_id,
                    'subject': 'python',
                    'total_lessons': 0,
                    'lessons': []
                }
                
                response = client.get(f'/api/users/{user_id}/subjects/python/lessons')
                # Should still work due to graceful degradation
                assert response.status_code == 200


class TestAPIPerformance:
    """Test API performance and resource usage"""
    
    def test_concurrent_user_creation(self, client):
        """Test handling of concurrent user creation requests"""
        import threading
        import time
        
        results = []
        
        def create_user(user_id):
            user_data = {
                'user_id': f'concurrent_user_{user_id}',
                'email': f'concurrent{user_id}@test.com'
            }
            
            response = client.post('/api/users',
                                 data=json.dumps(user_data),
                                 content_type='application/json')
            results.append(response.status_code)
        
        # Create multiple threads to simulate concurrent requests
        threads = []
        for i in range(5):
            thread = threading.Thread(target=create_user, args=(i,))
            threads.append(thread)
        
        # Start all threads
        for thread in threads:
            thread.start()
        
        # Wait for all threads to complete
        for thread in threads:
            thread.join()
        
        # All requests should succeed
        assert all(status == 201 for status in results)
    
    def test_large_survey_submission(self, client, setup_test_data):
        """Test handling of large survey submissions"""
        test_data = setup_test_data
        user_id = test_data['user_id']
        
        # Create large survey answers payload
        large_answers = {
            'answers': [
                {'question_id': i, 'answer': f'Answer {i}'}
                for i in range(100)  # 100 questions
            ]
        }
        
        with patch('app.services.survey_analysis_service.SurveyAnalysisService.process_survey_answers') as mock_analysis:
            mock_analysis.return_value = {
                'user_id': user_id,
                'subject': 'python',
                'skill_level': 'advanced',
                'accuracy': 85.0,
                'total_questions': 100,
                'correct_answers': 85,
                'topic_analysis': {},
                'recommendations': [],
                'processed_at': datetime.utcnow().isoformat()
            }
            
            response = client.post(f'/api/users/{user_id}/subjects/python/survey/submit',
                                 data=json.dumps(large_answers),
                                 content_type='application/json')
            
            assert response.status_code == 200
            data = json.loads(response.data)
            assert data['results']['total_questions'] == 100
    
    def test_api_response_time(self, client, setup_test_data):
        """Test API response times for common operations"""
        import time
        
        test_data = setup_test_data
        user_id = test_data['user_id']
        
        # Test user retrieval response time
        start_time = time.time()
        response = client.get(f'/api/users/{user_id}')
        end_time = time.time()
        
        assert response.status_code == 200
        response_time = end_time - start_time
        assert response_time < 1.0  # Should respond within 1 second
        
        # Test subscription status check response time
        start_time = time.time()
        response = client.get(f'/api/users/{user_id}/subscriptions/python/status')
        end_time = time.time()
        
        assert response.status_code == 200
        response_time = end_time - start_time
        assert response_time < 0.5  # Should respond within 0.5 seconds


class TestAPIDataIntegrity:
    """Test data integrity across API operations"""
    
    def test_user_data_consistency(self, client, app):
        """Test that user data remains consistent across operations"""
        # Create user
        user_data = {
            'user_id': 'consistency_user',
            'email': 'consistency@test.com'
        }
        
        response = client.post('/api/users',
                             data=json.dumps(user_data),
                             content_type='application/json')
        assert response.status_code == 201
        
        # Retrieve user and verify data
        response = client.get('/api/users/consistency_user')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['user']['user_id'] == 'consistency_user'
        assert data['user']['email'] == 'consistency@test.com'
        
        # Update user
        update_data = {'email': 'updated@test.com'}
        response = client.put('/api/users/consistency_user',
                            data=json.dumps(update_data),
                            content_type='application/json')
        assert response.status_code == 200
        
        # Verify update
        response = client.get('/api/users/consistency_user')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['user']['email'] == 'updated@test.com'
    
    def test_subscription_state_consistency(self, client, app):
        """Test subscription state consistency across operations"""
        with app.app_context():
            # Create user
            user = User(user_id='sub_consistency_user', email='subcon@test.com')
            db.session.add(user)
            db.session.commit()
        
        # Check initial subscription status
        response = client.get('/api/users/sub_consistency_user/subscriptions/python/status')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['has_active_subscription'] == False
        
        # Purchase subscription
        response = client.post('/api/users/sub_consistency_user/subscriptions/python')
        assert response.status_code == 201
        
        # Verify subscription is now active
        response = client.get('/api/users/sub_consistency_user/subscriptions/python/status')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['has_active_subscription'] == True
        
        # Cancel subscription
        response = client.delete('/api/users/sub_consistency_user/subscriptions/python')
        assert response.status_code == 200
        
        # Verify subscription is now cancelled
        response = client.get('/api/users/sub_consistency_user/subscriptions/python/status')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['has_active_subscription'] == False