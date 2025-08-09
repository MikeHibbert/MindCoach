import pytest
import json
import tempfile
import shutil
from unittest.mock import patch, MagicMock

from app import create_app, db
from app.models.user import User
from app.models.subscription import Subscription
from app.services.user_data_service import UserDataService


class TestSubjectsAPI:
    """Test cases for subjects API endpoints"""
    
    @pytest.fixture
    def app(self):
        """Create test Flask app"""
        app = create_app('testing')
        with app.app_context():
            db.create_all()
            yield app
            db.drop_all()
    
    @pytest.fixture
    def client(self, app):
        """Create test client"""
        return app.test_client()
    
    @pytest.fixture
    def temp_dir(self):
        """Create temporary directory for file operations"""
        temp_dir = tempfile.mkdtemp()
        yield temp_dir
        shutil.rmtree(temp_dir)
    
    @pytest.fixture
    def test_user(self, app):
        """Create test user"""
        with app.app_context():
            user = User(user_id='test-user-123', email='test@example.com')
            db.session.add(user)
            db.session.commit()
            return user
    
    @pytest.fixture
    def test_subscription(self, app, test_user):
        """Create test subscription"""
        with app.app_context():
            subscription = Subscription(
                user_id='test-user-123',
                subject='python',
                status='active'
            )
            db.session.add(subscription)
            db.session.commit()
            return subscription
    
    def test_list_subjects_without_user_id(self, client):
        """Test listing subjects without user_id parameter"""
        response = client.get('/api/subjects')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        
        assert 'subjects' in data
        assert 'total_count' in data
        assert len(data['subjects']) == 5  # All available subjects
        
        # All subjects should be locked by default
        for subject in data['subjects']:
            assert subject['locked'] is True
            assert 'id' in subject
            assert 'name' in subject
            assert 'description' in subject
            assert 'pricing' in subject
            assert 'available' in subject
    
    def test_list_subjects_with_user_id_no_subscriptions(self, client, test_user):
        """Test listing subjects with user_id but no subscriptions"""
        response = client.get('/api/subjects?user_id=test-user-123')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        
        assert len(data['subjects']) == 5
        
        # All subjects should be locked since user has no subscriptions
        for subject in data['subjects']:
            assert subject['locked'] is True
    
    def test_list_subjects_with_user_id_and_subscription(self, client, test_user, test_subscription):
        """Test listing subjects with user_id and active subscription"""
        response = client.get('/api/subjects?user_id=test-user-123')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        
        # Find Python subject (should be unlocked)
        python_subject = next(s for s in data['subjects'] if s['id'] == 'python')
        assert python_subject['locked'] is False
        
        # Other subjects should still be locked
        other_subjects = [s for s in data['subjects'] if s['id'] != 'python']
        for subject in other_subjects:
            assert subject['locked'] is True
    
    def test_list_subjects_with_invalid_user_id(self, client):
        """Test listing subjects with invalid user_id"""
        response = client.get('/api/subjects?user_id=invalid-user')
        
        # Should still return subjects but all locked
        assert response.status_code == 200
        data = json.loads(response.data)
        
        for subject in data['subjects']:
            assert subject['locked'] is True
    
    @patch('app.services.user_data_service.UserDataService.save_subject_selection')
    def test_select_subject_success(self, mock_save_selection, client, test_user, test_subscription):
        """Test successful subject selection"""
        mock_save_selection.return_value = True
        
        response = client.post('/api/users/test-user-123/subjects/python/select')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        
        assert 'message' in data
        assert 'subject' in data
        assert data['subject']['id'] == 'python'
        assert data['subject']['name'] == 'Python Programming'
        
        mock_save_selection.assert_called_once_with('test-user-123', 'python')
    
    def test_select_subject_no_subscription(self, client, test_user):
        """Test subject selection without subscription"""
        response = client.post('/api/users/test-user-123/subjects/python/select')
        
        assert response.status_code == 402  # Payment Required
        data = json.loads(response.data)
        
        assert data['error']['code'] == 'SUBSCRIPTION_REQUIRED'
        assert 'details' in data['error']
        assert data['error']['details']['subject'] == 'python'
    
    def test_select_subject_invalid_user_id(self, client):
        """Test subject selection with invalid user_id format"""
        response = client.post('/api/users/user@invalid.com/subjects/python/select')
        
        assert response.status_code == 400
        data = json.loads(response.data)
        assert data['error']['code'] == 'INVALID_USER_ID'
    
    def test_select_subject_invalid_subject(self, client, test_user):
        """Test subject selection with invalid subject"""
        response = client.post('/api/users/test-user-123/subjects/Invalid_Subject/select')
        
        assert response.status_code == 400
        data = json.loads(response.data)
        assert data['error']['code'] == 'INVALID_SUBJECT'
    
    def test_select_subject_nonexistent_subject(self, client, test_user):
        """Test subject selection with nonexistent subject"""
        response = client.post('/api/users/test-user-123/subjects/nonexistent/select')
        
        assert response.status_code == 404
        data = json.loads(response.data)
        assert data['error']['code'] == 'SUBJECT_NOT_FOUND'
    
    def test_select_subject_nonexistent_user(self, client):
        """Test subject selection with nonexistent user"""
        response = client.post('/api/users/nonexistent-user/subjects/python/select')
        
        assert response.status_code == 404
        data = json.loads(response.data)
        assert data['error']['code'] == 'USER_NOT_FOUND'
    
    @patch('app.services.user_data_service.UserDataService.save_subject_selection')
    def test_select_subject_save_failure(self, mock_save_selection, client, test_user, test_subscription):
        """Test subject selection when save fails"""
        mock_save_selection.return_value = False
        
        response = client.post('/api/users/test-user-123/subjects/python/select')
        
        assert response.status_code == 500
        data = json.loads(response.data)
        assert data['error']['code'] == 'SELECTION_FAILED'
    
    def test_get_subject_status_with_subscription(self, client, test_user, test_subscription):
        """Test getting subject status with active subscription"""
        # First select the subject
        UserDataService.save_subject_selection('test-user-123', 'python')
        
        response = client.get('/api/users/test-user-123/subjects/python/status')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        
        assert data['user_id'] == 'test-user-123'
        assert data['subject']['id'] == 'python'
        assert data['access_status']['has_active_subscription'] is True
        assert data['access_status']['is_selected'] is True
        assert data['access_status']['can_access_lessons'] is True
        assert data['access_status']['requires_payment'] is False
        assert data['subscription'] is not None
    
    def test_get_subject_status_without_subscription(self, client, test_user):
        """Test getting subject status without subscription"""
        response = client.get('/api/users/test-user-123/subjects/python/status')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        
        assert data['access_status']['has_active_subscription'] is False
        assert data['access_status']['requires_payment'] is True
        assert data['access_status']['can_access_lessons'] is False
        assert data['subscription'] is None
    
    def test_get_subject_status_invalid_user(self, client):
        """Test getting subject status with invalid user"""
        response = client.get('/api/users/user@invalid.com/subjects/python/status')
        
        assert response.status_code == 400
        data = json.loads(response.data)
        assert data['error']['code'] == 'INVALID_USER_ID'
    
    def test_get_subject_status_nonexistent_user(self, client):
        """Test getting subject status with nonexistent user"""
        response = client.get('/api/users/nonexistent-user/subjects/python/status')
        
        assert response.status_code == 404
        data = json.loads(response.data)
        assert data['error']['code'] == 'USER_NOT_FOUND'
    
    def test_check_subject_access_with_subscription(self, client, test_user, test_subscription):
        """Test checking subject access with active subscription"""
        response = client.get('/api/users/test-user-123/subjects/python/access')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        
        assert data['access_granted'] is True
        assert data['subject']['id'] == 'python'
    
    def test_check_subject_access_without_subscription(self, client, test_user):
        """Test checking subject access without subscription"""
        response = client.get('/api/users/test-user-123/subjects/python/access')
        
        assert response.status_code == 402  # Payment Required
        data = json.loads(response.data)
        
        assert data['access_granted'] is False
        assert data['reason'] == 'SUBSCRIPTION_REQUIRED'
        assert 'subscription_options' in data
    
    def test_check_subject_access_invalid_user(self, client):
        """Test checking subject access with invalid user"""
        response = client.get('/api/users/user@invalid.com/subjects/python/access')
        
        assert response.status_code == 400
        data = json.loads(response.data)
        assert data['error']['code'] == 'INVALID_USER_ID'
    
    def test_check_subject_access_nonexistent_user(self, client):
        """Test checking subject access with nonexistent user"""
        response = client.get('/api/users/nonexistent-user/subjects/python/access')
        
        assert response.status_code == 404
        data = json.loads(response.data)
        assert data['error']['code'] == 'USER_NOT_FOUND'
    
    def test_subject_selection_integration_flow(self, client, test_user, test_subscription):
        """Test complete subject selection integration flow"""
        # 1. List subjects - Python should be unlocked
        response = client.get('/api/subjects?user_id=test-user-123')
        assert response.status_code == 200
        data = json.loads(response.data)
        python_subject = next(s for s in data['subjects'] if s['id'] == 'python')
        assert python_subject['locked'] is False
        
        # 2. Select Python subject
        response = client.post('/api/users/test-user-123/subjects/python/select')
        assert response.status_code == 200
        
        # 3. Check subject status - should show selected and accessible
        response = client.get('/api/users/test-user-123/subjects/python/status')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['access_status']['is_selected'] is True
        assert data['access_status']['can_access_lessons'] is True
        
        # 4. Check access - should be granted
        response = client.get('/api/users/test-user-123/subjects/python/access')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['access_granted'] is True