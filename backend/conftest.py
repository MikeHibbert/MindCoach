"""
Pytest configuration and fixtures for the backend test suite
"""

import pytest
import tempfile
import os
import shutil
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock

# Import Flask app and database
from app import create_app, db
from app.models.user import User
from app.models.subscription import Subscription
from app.models.survey_result import SurveyResult


@pytest.fixture(scope='session')
def app():
    """Create application for testing"""
    # Create temporary directory for test database
    test_dir = tempfile.mkdtemp()
    test_db_path = os.path.join(test_dir, 'test.db')
    
    # Configure app for testing
    config = {
        'TESTING': True,
        'SQLALCHEMY_DATABASE_URI': f'sqlite:///{test_db_path}',
        'SQLALCHEMY_TRACK_MODIFICATIONS': False,
        'WTF_CSRF_ENABLED': False,
        'SECRET_KEY': 'test-secret-key'
    }
    
    app = create_app(config)
    
    with app.app_context():
        # Create all tables
        db.create_all()
        yield app
        
        # Cleanup
        db.drop_all()
    
    # Remove temporary directory
    shutil.rmtree(test_dir)


@pytest.fixture(scope='function')
def client(app):
    """Create test client"""
    return app.test_client()


@pytest.fixture(scope='function')
def db_session(app):
    """Create database session for testing"""
    with app.app_context():
        # Start a transaction
        connection = db.engine.connect()
        transaction = connection.begin()
        
        # Configure session to use the transaction
        session = db.create_scoped_session(
            options={"bind": connection, "binds": {}}
        )
        db.session = session
        
        yield session
        
        # Rollback transaction and close connection
        transaction.rollback()
        connection.close()
        session.remove()


@pytest.fixture(scope='function')
def test_user(db_session):
    """Create a test user"""
    user = User(
        user_id='test-user-123',
        email='test@example.com'
    )
    db_session.add(user)
    db_session.commit()
    
    # Refresh to ensure all attributes are loaded
    db_session.refresh(user)
    return user


@pytest.fixture(scope='function')
def test_user_with_subscription(db_session):
    """Create a test user with an active subscription"""
    user = User(
        user_id='test-user-with-sub',
        email='subscriber@example.com'
    )
    db_session.add(user)
    db_session.flush()  # Get the user ID
    
    subscription = Subscription(
        user_id=user.user_id,
        subject='python',
        status='active',
        expires_at=datetime.utcnow() + timedelta(days=30)
    )
    db_session.add(subscription)
    db_session.commit()
    
    # Refresh to ensure all attributes are loaded
    db_session.refresh(user)
    return user


@pytest.fixture(scope='function')
def test_expired_subscription(db_session, test_user):
    """Create an expired subscription for test user"""
    subscription = Subscription(
        user_id=test_user.user_id,
        subject='javascript',
        status='active',
        expires_at=datetime.utcnow() - timedelta(days=1)
    )
    db_session.add(subscription)
    db_session.commit()
    return subscription


@pytest.fixture(scope='function')
def test_survey_result(db_session, test_user):
    """Create a test survey result"""
    survey_result = SurveyResult(
        user_id=test_user.user_id,
        subject='python',
        skill_level='intermediate'
    )
    db_session.add(survey_result)
    db_session.commit()
    return survey_result


@pytest.fixture(scope='function')
def temp_user_directory():
    """Create temporary user directory for file operations"""
    temp_dir = tempfile.mkdtemp()
    user_dir = os.path.join(temp_dir, 'users', 'test-user-123')
    os.makedirs(user_dir, exist_ok=True)
    
    yield user_dir
    
    # Cleanup
    shutil.rmtree(temp_dir)


@pytest.fixture(scope='function')
def mock_file_service():
    """Mock file service operations"""
    with patch('app.services.file_service.FileService') as mock:
        mock_instance = MagicMock()
        mock.return_value = mock_instance
        
        # Configure common return values
        mock_instance.save_json.return_value = True
        mock_instance.load_json.return_value = {'test': 'data'}
        mock_instance.save_text.return_value = True
        mock_instance.load_text.return_value = 'test content'
        mock_instance.file_exists.return_value = True
        mock_instance.create_directory.return_value = True
        
        yield mock_instance


@pytest.fixture(scope='function')
def mock_lesson_generation():
    """Mock lesson generation service"""
    with patch('app.services.lesson_generation_service.LessonGenerationService') as mock:
        mock_instance = MagicMock()
        mock.return_value = mock_instance
        
        # Configure return values
        mock_instance.generate_lessons.return_value = {
            'success': True,
            'lessons_generated': 10,
            'skill_level': 'intermediate'
        }
        
        yield mock_instance


@pytest.fixture(scope='function')
def mock_survey_generation():
    """Mock survey generation service"""
    with patch('app.services.survey_generation_service.SurveyGenerationService') as mock:
        mock_instance = MagicMock()
        mock.return_value = mock_instance
        
        # Configure return values
        mock_instance.generate_survey.return_value = {
            'questions': [
                {
                    'id': 1,
                    'question': 'What is Python?',
                    'type': 'multiple_choice',
                    'options': ['Language', 'Snake', 'Tool', 'Framework']
                }
            ]
        }
        
        yield mock_instance


@pytest.fixture(scope='function')
def sample_survey_data():
    """Sample survey data for testing"""
    return {
        'questions': [
            {
                'id': 1,
                'question': 'What is a Python list?',
                'type': 'multiple_choice',
                'options': ['Array', 'Dictionary', 'Ordered collection', 'Function'],
                'difficulty': 'beginner'
            },
            {
                'id': 2,
                'question': 'How do you define a function in Python?',
                'type': 'multiple_choice',
                'options': ['function myFunc()', 'def myFunc():', 'func myFunc()', 'define myFunc()'],
                'difficulty': 'intermediate'
            }
        ]
    }


@pytest.fixture(scope='function')
def sample_survey_answers():
    """Sample survey answers for testing"""
    return {
        'answers': [
            {'question_id': 1, 'answer': 'Ordered collection', 'correct': True},
            {'question_id': 2, 'answer': 'def myFunc():', 'correct': True}
        ],
        'skill_level': 'intermediate',
        'score': 100
    }


@pytest.fixture(scope='function')
def sample_lesson_data():
    """Sample lesson data for testing"""
    return {
        'lesson_number': 1,
        'title': 'Introduction to Python',
        'content': '# Introduction to Python\n\nPython is a programming language...',
        'estimated_time': '30 minutes',
        'difficulty': 'beginner',
        'topics': ['variables', 'data types', 'basic syntax']
    }


@pytest.fixture(scope='function')
def performance_timer():
    """Timer fixture for performance testing"""
    import time
    
    class Timer:
        def __init__(self):
            self.start_time = None
            self.end_time = None
        
        def start(self):
            self.start_time = time.time()
        
        def stop(self):
            self.end_time = time.time()
        
        @property
        def elapsed(self):
            if self.start_time and self.end_time:
                return self.end_time - self.start_time
            return None
    
    return Timer()


# Utility functions for tests
def create_test_subscription(db_session, user_id, subject, status='active', days_offset=30):
    """Helper function to create test subscriptions"""
    subscription = Subscription(
        user_id=user_id,
        subject=subject,
        status=status,
        expires_at=datetime.utcnow() + timedelta(days=days_offset)
    )
    db_session.add(subscription)
    db_session.commit()
    return subscription


def create_test_survey_result(db_session, user_id, subject, skill_level='intermediate'):
    """Helper function to create test survey results"""
    survey_result = SurveyResult(
        user_id=user_id,
        subject=subject,
        skill_level=skill_level
    )
    db_session.add(survey_result)
    db_session.commit()
    return survey_result


# Markers for different test types
pytest.mark.unit = pytest.mark.unit
pytest.mark.integration = pytest.mark.integration
pytest.mark.api = pytest.mark.api
pytest.mark.database = pytest.mark.database
pytest.mark.performance = pytest.mark.performance
pytest.mark.slow = pytest.mark.slow