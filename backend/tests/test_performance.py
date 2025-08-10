"""
Performance tests for backend services and API endpoints
Tests response times, memory usage, and scalability
"""

import pytest
import time
import threading
import json
import tempfile
import shutil
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock
import psutil
import os

from app import create_app, db
from app.models.user import User
from app.models.subscription import Subscription
from app.services.lesson_generation_service import LessonGenerationService
from app.services.survey_generation_service import SurveyGenerationService
from app.services.file_service import FileService


@pytest.fixture(scope='function')
def app():
    """Create test Flask application"""
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
        
        with patch('app.services.file_service.FileService.BASE_DIR') as mock_base_dir:
            mock_base_dir.return_value = test_dir
            yield app
        
        db.drop_all()
    
    shutil.rmtree(test_dir, ignore_errors=True)


@pytest.fixture(scope='function')
def client(app):
    """Create test client"""
    return app.test_client()


class PerformanceTimer:
    """Helper class for measuring performance"""
    
    def __init__(self):
        self.start_time = None
        self.end_time = None
        self.start_memory = None
        self.end_memory = None
    
    def start(self):
        """Start timing and memory measurement"""
        self.start_time = time.time()
        process = psutil.Process(os.getpid())
        self.start_memory = process.memory_info().rss / 1024 / 1024  # MB
    
    def stop(self):
        """Stop timing and memory measurement"""
        self.end_time = time.time()
        process = psutil.Process(os.getpid())
        self.end_memory = process.memory_info().rss / 1024 / 1024  # MB
    
    @property
    def elapsed_time(self):
        """Get elapsed time in seconds"""
        if self.start_time and self.end_time:
            return self.end_time - self.start_time
        return None
    
    @property
    def memory_delta(self):
        """Get memory usage change in MB"""
        if self.start_memory and self.end_memory:
            return self.end_memory - self.start_memory
        return None


@pytest.mark.performance
class TestAPIPerformance:
    """Test API endpoint performance"""
    
    def test_user_creation_performance(self, client):
        """Test user creation API performance"""
        timer = PerformanceTimer()
        
        user_data = {
            'user_id': 'perf_test_user',
            'email': 'perf@test.com'
        }
        
        timer.start()
        response = client.post('/api/users',
                             data=json.dumps(user_data),
                             content_type='application/json')
        timer.stop()
        
        assert response.status_code == 201
        assert timer.elapsed_time < 0.5  # Should complete within 500ms
        assert timer.memory_delta < 10   # Should not use more than 10MB additional memory
    
    def test_user_retrieval_performance(self, client, app):
        """Test user retrieval API performance"""
        # Create test user first
        with app.app_context():
            user = User(user_id='perf_retrieve_user', email='retrieve@test.com')
            db.session.add(user)
            db.session.commit()
        
        timer = PerformanceTimer()
        
        timer.start()
        response = client.get('/api/users/perf_retrieve_user')
        timer.stop()
        
        assert response.status_code == 200
        assert timer.elapsed_time < 0.2  # Should complete within 200ms
        assert timer.memory_delta < 5    # Should not use more than 5MB additional memory
    
    def test_subscription_check_performance(self, client, app):
        """Test subscription status check performance"""
        with app.app_context():
            user = User(user_id='perf_sub_user', email='sub@test.com')
            db.session.add(user)
            
            subscription = Subscription(
                user_id='perf_sub_user',
                subject='python',
                status='active',
                expires_at=datetime.utcnow() + timedelta(days=30)
            )
            db.session.add(subscription)
            db.session.commit()
        
        timer = PerformanceTimer()
        
        timer.start()
        response = client.get('/api/users/perf_sub_user/subscriptions/python/status')
        timer.stop()
        
        assert response.status_code == 200
        assert timer.elapsed_time < 0.3  # Should complete within 300ms
        assert timer.memory_delta < 5    # Should not use more than 5MB additional memory
    
    def test_concurrent_api_requests(self, client, app):
        """Test API performance under concurrent load"""
        # Create test users first
        with app.app_context():
            for i in range(10):
                user = User(user_id=f'concurrent_user_{i}', email=f'concurrent{i}@test.com')
                db.session.add(user)
            db.session.commit()
        
        results = []
        
        def make_request(user_id):
            start_time = time.time()
            response = client.get(f'/api/users/concurrent_user_{user_id}')
            end_time = time.time()
            
            results.append({
                'status_code': response.status_code,
                'response_time': end_time - start_time
            })
        
        # Create and start threads
        threads = []
        for i in range(10):
            thread = threading.Thread(target=make_request, args=(i,))
            threads.append(thread)
        
        start_time = time.time()
        for thread in threads:
            thread.start()
        
        for thread in threads:
            thread.join()
        end_time = time.time()
        
        # All requests should succeed
        assert all(result['status_code'] == 200 for result in results)
        
        # Total time should be reasonable (concurrent execution)
        total_time = end_time - start_time
        assert total_time < 2.0  # Should complete within 2 seconds
        
        # Individual response times should be reasonable
        avg_response_time = sum(result['response_time'] for result in results) / len(results)
        assert avg_response_time < 0.5  # Average response time should be under 500ms


@pytest.mark.performance
class TestServicePerformance:
    """Test service layer performance"""
    
    def test_lesson_generation_performance(self, app):
        """Test lesson generation service performance"""
        with app.app_context():
            timer = PerformanceTimer()
            
            # Mock the actual AI generation to focus on service logic performance
            with patch('app.services.lesson_generation_service.LessonGenerationService._generate_lesson_content') as mock_generate:
                mock_generate.return_value = {
                    'title': 'Test Lesson',
                    'content': '# Test Lesson\nThis is test content.',
                    'estimated_time': '30 minutes',
                    'difficulty': 'intermediate',
                    'topics': ['test_topic']
                }
                
                timer.start()
                result = LessonGenerationService.generate_personalized_lessons('test_user', 'python')
                timer.stop()
                
                assert result is not None
                assert timer.elapsed_time < 2.0  # Should complete within 2 seconds
                assert timer.memory_delta < 20   # Should not use more than 20MB additional memory
    
    def test_survey_generation_performance(self, app):
        """Test survey generation service performance"""
        with app.app_context():
            timer = PerformanceTimer()
            
            # Mock the actual AI generation
            with patch('app.services.survey_generation_service.SurveyGenerationService._generate_questions') as mock_generate:
                mock_generate.return_value = [
                    {
                        'id': 1,
                        'question': 'What is Python?',
                        'type': 'multiple_choice',
                        'options': ['Language', 'Snake', 'Tool', 'Framework'],
                        'correct_answer': 'Language'
                    }
                ]
                
                timer.start()
                result = SurveyGenerationService.generate_survey('python', 'test_user')
                timer.stop()
                
                assert result is not None
                assert timer.elapsed_time < 1.0  # Should complete within 1 second
                assert timer.memory_delta < 10   # Should not use more than 10MB additional memory
    
    def test_file_operations_performance(self, app):
        """Test file service operations performance"""
        timer = PerformanceTimer()
        
        # Test large JSON file operations
        large_data = {
            'lessons': [
                {
                    'lesson_number': i,
                    'title': f'Lesson {i}',
                    'content': 'A' * 1000,  # 1KB of content per lesson
                    'topics': [f'topic_{j}' for j in range(10)]
                }
                for i in range(100)  # 100 lessons
            ]
        }
        
        with tempfile.TemporaryDirectory() as temp_dir:
            file_path = os.path.join(temp_dir, 'large_data.json')
            
            timer.start()
            FileService.save_json(file_path, large_data)
            loaded_data = FileService.load_json(file_path)
            timer.stop()
            
            assert loaded_data == large_data
            assert timer.elapsed_time < 1.0  # Should complete within 1 second
            assert timer.memory_delta < 50   # Should not use more than 50MB additional memory
    
    def test_database_operations_performance(self, app):
        """Test database operations performance"""
        with app.app_context():
            timer = PerformanceTimer()
            
            timer.start()
            
            # Create multiple users
            users = []
            for i in range(100):
                user = User(user_id=f'perf_db_user_{i}', email=f'perfdb{i}@test.com')
                users.append(user)
                db.session.add(user)
            
            db.session.commit()
            
            # Query users
            retrieved_users = User.query.filter(User.user_id.like('perf_db_user_%')).all()
            
            timer.stop()
            
            assert len(retrieved_users) == 100
            assert timer.elapsed_time < 2.0  # Should complete within 2 seconds
            assert timer.memory_delta < 30   # Should not use more than 30MB additional memory


@pytest.mark.performance
class TestMemoryUsage:
    """Test memory usage patterns"""
    
    def test_memory_leak_detection(self, client, app):
        """Test for memory leaks in repeated operations"""
        initial_memory = psutil.Process(os.getpid()).memory_info().rss / 1024 / 1024
        
        # Perform repeated operations
        for i in range(50):
            user_data = {
                'user_id': f'memory_test_user_{i}',
                'email': f'memory{i}@test.com'
            }
            
            response = client.post('/api/users',
                                 data=json.dumps(user_data),
                                 content_type='application/json')
            assert response.status_code == 201
            
            # Retrieve the user
            response = client.get(f'/api/users/memory_test_user_{i}')
            assert response.status_code == 200
        
        final_memory = psutil.Process(os.getpid()).memory_info().rss / 1024 / 1024
        memory_increase = final_memory - initial_memory
        
        # Memory increase should be reasonable (less than 100MB for 50 operations)
        assert memory_increase < 100
    
    def test_large_data_handling(self, app):
        """Test handling of large data structures"""
        with app.app_context():
            initial_memory = psutil.Process(os.getpid()).memory_info().rss / 1024 / 1024
            
            # Create large data structure
            large_lesson_data = {
                'lessons': [
                    {
                        'lesson_number': i,
                        'title': f'Lesson {i}',
                        'content': 'X' * 10000,  # 10KB per lesson
                        'topics': [f'topic_{j}' for j in range(50)]
                    }
                    for i in range(500)  # 500 lessons = ~5MB of data
                ]
            }
            
            # Process the data
            processed_lessons = []
            for lesson in large_lesson_data['lessons']:
                processed_lesson = {
                    'number': lesson['lesson_number'],
                    'title': lesson['title'],
                    'content_length': len(lesson['content']),
                    'topic_count': len(lesson['topics'])
                }
                processed_lessons.append(processed_lesson)
            
            final_memory = psutil.Process(os.getpid()).memory_info().rss / 1024 / 1024
            memory_increase = final_memory - initial_memory
            
            # Memory increase should be proportional to data size
            assert memory_increase < 50  # Should not use more than 50MB for processing


@pytest.mark.performance
class TestScalability:
    """Test system scalability"""
    
    def test_user_scalability(self, client, app):
        """Test system performance with increasing number of users"""
        response_times = []
        
        # Test with increasing number of users
        for batch_size in [10, 50, 100]:
            # Create users in batch
            with app.app_context():
                for i in range(batch_size):
                    user = User(
                        user_id=f'scale_user_{batch_size}_{i}',
                        email=f'scale{batch_size}_{i}@test.com'
                    )
                    db.session.add(user)
                db.session.commit()
            
            # Measure response time for user retrieval
            start_time = time.time()
            response = client.get(f'/api/users/scale_user_{batch_size}_0')
            end_time = time.time()
            
            assert response.status_code == 200
            response_times.append(end_time - start_time)
        
        # Response times should not degrade significantly with more users
        # Allow for some variation but ensure it doesn't grow exponentially
        assert all(rt < 1.0 for rt in response_times)  # All under 1 second
        
        # The last response time should not be more than 3x the first
        if len(response_times) >= 2:
            assert response_times[-1] < response_times[0] * 3
    
    def test_concurrent_lesson_generation(self, client, app):
        """Test concurrent lesson generation performance"""
        # Create test users with subscriptions
        with app.app_context():
            for i in range(5):
                user = User(user_id=f'concurrent_lesson_user_{i}', email=f'lesson{i}@test.com')
                db.session.add(user)
                
                subscription = Subscription(
                    user_id=f'concurrent_lesson_user_{i}',
                    subject='python',
                    status='active',
                    expires_at=datetime.utcnow() + timedelta(days=30)
                )
                db.session.add(subscription)
            
            db.session.commit()
        
        results = []
        
        def generate_lessons(user_id):
            with patch('app.services.lesson_generation_service.LessonGenerationService.generate_personalized_lessons') as mock_gen, \
                 patch('app.services.lesson_file_service.LessonFileService.save_lessons') as mock_save:
                
                mock_gen.return_value = {
                    'lessons': [{'lesson_number': 1, 'title': 'Test', 'content': 'Content'}],
                    'metadata': {'skill_level': 'intermediate', 'total_lessons': 1, 'generated_at': datetime.utcnow().isoformat(), 'topic_analysis': {}}
                }
                mock_save.return_value = {'saved_successfully': 1, 'failed_saves': 0, 'saved_files': ['lesson_1.md'], 'failed_files': []}
                
                start_time = time.time()
                response = client.post(f'/api/users/concurrent_lesson_user_{user_id}/subjects/python/lessons/generate')
                end_time = time.time()
                
                results.append({
                    'status_code': response.status_code,
                    'response_time': end_time - start_time
                })
        
        # Start concurrent lesson generation
        threads = []
        for i in range(5):
            thread = threading.Thread(target=generate_lessons, args=(i,))
            threads.append(thread)
        
        start_time = time.time()
        for thread in threads:
            thread.start()
        
        for thread in threads:
            thread.join()
        end_time = time.time()
        
        # All requests should succeed
        assert all(result['status_code'] == 201 for result in results)
        
        # Total time should be reasonable for concurrent execution
        total_time = end_time - start_time
        assert total_time < 5.0  # Should complete within 5 seconds
        
        # Individual response times should be reasonable
        max_response_time = max(result['response_time'] for result in results)
        assert max_response_time < 3.0  # No single request should take more than 3 seconds


@pytest.mark.performance
class TestResourceUsage:
    """Test resource usage patterns"""
    
    def test_cpu_usage_during_operations(self, client, app):
        """Test CPU usage during intensive operations"""
        # This test would ideally use more sophisticated CPU monitoring
        # For now, we'll test that operations complete within reasonable time
        
        with app.app_context():
            # Create test data
            for i in range(20):
                user = User(user_id=f'cpu_test_user_{i}', email=f'cpu{i}@test.com')
                db.session.add(user)
            db.session.commit()
        
        start_time = time.time()
        
        # Perform CPU-intensive operations
        for i in range(20):
            response = client.get(f'/api/users/cpu_test_user_{i}')
            assert response.status_code == 200
            
            # Simulate some processing
            data = json.loads(response.data)
            processed_data = {
                'user_id': data['user']['user_id'],
                'email_domain': data['user']['email'].split('@')[1] if data['user']['email'] else None,
                'created_timestamp': data['user'].get('created_at')
            }
        
        end_time = time.time()
        total_time = end_time - start_time
        
        # Operations should complete within reasonable time
        assert total_time < 2.0  # Should complete within 2 seconds
    
    def test_disk_io_performance(self, app):
        """Test disk I/O performance for file operations"""
        with tempfile.TemporaryDirectory() as temp_dir:
            timer = PerformanceTimer()
            
            # Test writing multiple files
            timer.start()
            
            for i in range(50):
                file_path = os.path.join(temp_dir, f'test_file_{i}.json')
                test_data = {
                    'file_number': i,
                    'content': f'This is test content for file {i}',
                    'data': list(range(100))  # Some data to make file larger
                }
                
                FileService.save_json(file_path, test_data)
            
            # Test reading files
            for i in range(50):
                file_path = os.path.join(temp_dir, f'test_file_{i}.json')
                loaded_data = FileService.load_json(file_path)
                assert loaded_data['file_number'] == i
            
            timer.stop()
            
            assert timer.elapsed_time < 3.0  # Should complete within 3 seconds
            assert timer.memory_delta < 30   # Should not use more than 30MB additional memory