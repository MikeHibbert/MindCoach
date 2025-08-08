"""
Tests for user API endpoints
"""

import pytest
import json
import os
import tempfile
import shutil
from app import create_app, db
from app.models.user import User


@pytest.fixture
def app():
    """Create test Flask application"""
    app = create_app()
    app.config['TESTING'] = True
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    
    with app.app_context():
        db.create_all()
        yield app
        db.drop_all()


@pytest.fixture
def client(app):
    """Create test client"""
    return app.test_client()


@pytest.fixture
def temp_users_dir():
    """Create temporary users directory for testing"""
    temp_dir = tempfile.mkdtemp()
    users_dir = os.path.join(temp_dir, 'users')
    os.makedirs(users_dir, exist_ok=True)
    
    # Mock the base directory path
    original_path = None
    try:
        from app.services.file_service import FileService
        from pathlib import Path
        original_path = FileService.BASE_DIR
        FileService.BASE_DIR = Path(users_dir)
        yield users_dir
    finally:
        if original_path:
            FileService.BASE_DIR = original_path
        shutil.rmtree(temp_dir)


class TestUserAPI:
    """Test cases for user API endpoints"""
    
    def test_create_user_success(self, client, temp_users_dir):
        """Test successful user creation"""
        user_data = {
            'user_id': 'test_user_123',
            'email': 'test@example.com'
        }
        
        response = client.post('/api/users', 
                             data=json.dumps(user_data),
                             content_type='application/json')
        
        assert response.status_code == 201
        data = json.loads(response.data)
        assert data['message'] == 'User created successfully'
        assert data['user']['user_id'] == 'test_user_123'
        assert data['user']['email'] == 'test@example.com'
        
        # Verify user directory was created
        user_dir = os.path.join(temp_users_dir, 'test_user_123')
        assert os.path.exists(user_dir)
    
    def test_create_user_without_email(self, client, temp_users_dir):
        """Test user creation without email"""
        user_data = {
            'user_id': 'test_user_456'
        }
        
        response = client.post('/api/users',
                             data=json.dumps(user_data),
                             content_type='application/json')
        
        assert response.status_code == 201
        data = json.loads(response.data)
        assert data['user']['user_id'] == 'test_user_456'
        assert data['user']['email'] is None
    
    def test_create_user_invalid_user_id(self, client):
        """Test user creation with invalid user_id"""
        user_data = {
            'user_id': 'invalid user id!',  # Contains spaces and special chars
            'email': 'test@example.com'
        }
        
        response = client.post('/api/users',
                             data=json.dumps(user_data),
                             content_type='application/json')
        
        assert response.status_code == 400
        data = json.loads(response.data)
        # The validation happens at the marshmallow level first
        assert data['error']['code'] == 'VALIDATION_ERROR'
    
    def test_create_user_missing_user_id(self, client):
        """Test user creation without user_id"""
        user_data = {
            'email': 'test@example.com'
        }
        
        response = client.post('/api/users',
                             data=json.dumps(user_data),
                             content_type='application/json')
        
        assert response.status_code == 400
        data = json.loads(response.data)
        assert data['error']['code'] == 'VALIDATION_ERROR'
    
    def test_create_user_invalid_email(self, client):
        """Test user creation with invalid email"""
        user_data = {
            'user_id': 'test_user_789',
            'email': 'invalid-email'
        }
        
        response = client.post('/api/users',
                             data=json.dumps(user_data),
                             content_type='application/json')
        
        assert response.status_code == 400
        data = json.loads(response.data)
        assert data['error']['code'] == 'VALIDATION_ERROR'
    
    def test_create_user_duplicate(self, client, temp_users_dir):
        """Test creating duplicate user returns existing user"""
        user_data = {
            'user_id': 'duplicate_user',
            'email': 'test@example.com'
        }
        
        # Create user first time
        response1 = client.post('/api/users',
                              data=json.dumps(user_data),
                              content_type='application/json')
        assert response1.status_code == 201
        
        # Try to create same user again
        response2 = client.post('/api/users',
                              data=json.dumps(user_data),
                              content_type='application/json')
        assert response2.status_code == 201
        data = json.loads(response2.data)
        assert data['user']['user_id'] == 'duplicate_user'
    
    def test_create_user_invalid_content_type(self, client):
        """Test user creation with invalid content type"""
        response = client.post('/api/users',
                             data='user_id=test',
                             content_type='application/x-www-form-urlencoded')
        
        assert response.status_code == 400
        data = json.loads(response.data)
        assert data['error']['code'] == 'INVALID_CONTENT_TYPE'
    
    def test_get_user_success(self, client, temp_users_dir):
        """Test successful user retrieval"""
        # Create user first
        user_data = {
            'user_id': 'get_test_user',
            'email': 'get@example.com'
        }
        client.post('/api/users',
                   data=json.dumps(user_data),
                   content_type='application/json')
        
        # Get user
        response = client.get('/api/users/get_test_user')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['user']['user_id'] == 'get_test_user'
        assert data['user']['email'] == 'get@example.com'
    
    def test_get_user_not_found(self, client):
        """Test getting non-existent user"""
        response = client.get('/api/users/nonexistent_user')
        
        assert response.status_code == 404
        data = json.loads(response.data)
        assert data['error']['code'] == 'USER_NOT_FOUND'
    
    def test_get_user_invalid_user_id(self, client):
        """Test getting user with invalid user_id"""
        response = client.get('/api/users/invalid user id!')
        
        assert response.status_code == 400
        data = json.loads(response.data)
        assert data['error']['code'] == 'INVALID_USER_ID'
    
    def test_update_user_success(self, client, temp_users_dir):
        """Test successful user update"""
        # Create user first
        user_data = {
            'user_id': 'update_test_user',
            'email': 'original@example.com'
        }
        client.post('/api/users',
                   data=json.dumps(user_data),
                   content_type='application/json')
        
        # Update user
        update_data = {
            'email': 'updated@example.com'
        }
        response = client.put('/api/users/update_test_user',
                            data=json.dumps(update_data),
                            content_type='application/json')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['message'] == 'User updated successfully'
        assert data['user']['email'] == 'updated@example.com'
    
    def test_update_user_not_found(self, client):
        """Test updating non-existent user"""
        update_data = {
            'email': 'updated@example.com'
        }
        response = client.put('/api/users/nonexistent_user',
                            data=json.dumps(update_data),
                            content_type='application/json')
        
        assert response.status_code == 404
        data = json.loads(response.data)
        assert data['error']['code'] == 'USER_NOT_FOUND'
    
    def test_update_user_invalid_user_id(self, client):
        """Test updating user with invalid user_id"""
        update_data = {
            'email': 'updated@example.com'
        }
        response = client.put('/api/users/invalid user id!',
                            data=json.dumps(update_data),
                            content_type='application/json')
        
        assert response.status_code == 400
        data = json.loads(response.data)
        assert data['error']['code'] == 'INVALID_USER_ID'
    
    def test_update_user_invalid_email(self, client, temp_users_dir):
        """Test updating user with invalid email"""
        # Create user first
        user_data = {
            'user_id': 'email_test_user',
            'email': 'original@example.com'
        }
        client.post('/api/users',
                   data=json.dumps(user_data),
                   content_type='application/json')
        
        # Try to update with invalid email
        update_data = {
            'email': 'invalid-email'
        }
        response = client.put('/api/users/email_test_user',
                            data=json.dumps(update_data),
                            content_type='application/json')
        
        assert response.status_code == 400
        data = json.loads(response.data)
        assert data['error']['code'] == 'VALIDATION_ERROR'
    
    def test_update_user_empty_data(self, client, temp_users_dir):
        """Test updating user with empty data"""
        # Create user first
        user_data = {
            'user_id': 'empty_update_user',
            'email': 'original@example.com'
        }
        client.post('/api/users',
                   data=json.dumps(user_data),
                   content_type='application/json')
        
        # Update with empty data
        update_data = {}
        response = client.put('/api/users/empty_update_user',
                            data=json.dumps(update_data),
                            content_type='application/json')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['user']['email'] == 'original@example.com'  # Should remain unchanged