"""
Tests for subscription API endpoints
"""

import pytest
import json
from datetime import datetime, timedelta
from app import create_app, db
from app.models.user import User
from app.models.subscription import Subscription


@pytest.fixture
def app():
    """Create application for testing"""
    app = create_app('testing')
    with app.app_context():
        db.create_all()
        yield app
        db.drop_all()


@pytest.fixture
def client(app):
    """Create test client"""
    return app.test_client()


@pytest.fixture
def sample_user(app):
    """Create a sample user for testing"""
    with app.app_context():
        user = User(user_id='test-user', email='test@example.com')
        db.session.add(user)
        db.session.commit()
        return user


@pytest.fixture
def sample_subscription(app, sample_user):
    """Create a sample subscription for testing"""
    with app.app_context():
        subscription = Subscription(
            user_id='test-user',
            subject='python',
            status='active',
            expires_at=datetime.utcnow() + timedelta(days=30)
        )
        db.session.add(subscription)
        db.session.commit()
        return subscription


class TestGetUserSubscriptions:
    """Test GET /api/users/<user_id>/subscriptions"""

    def test_get_user_subscriptions_success(self, client, sample_user, sample_subscription):
        """Test successful retrieval of user subscriptions"""
        response = client.get('/api/users/test-user/subscriptions')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        
        assert data['user_id'] == 'test-user'
        assert len(data['subscriptions']) == 1
        assert len(data['active_subscriptions']) == 1
        assert data['total_subscriptions'] == 1
        assert data['active_count'] == 1
        
        subscription = data['subscriptions'][0]
        assert subscription['user_id'] == 'test-user'
        assert subscription['subject'] == 'python'
        assert subscription['status'] == 'active'
        assert 'subject_info' in subscription
        assert subscription['subject_info']['name'] == 'Python Programming'

    def test_get_user_subscriptions_no_subscriptions(self, client, sample_user):
        """Test retrieval when user has no subscriptions"""
        response = client.get('/api/users/test-user/subscriptions')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        
        assert data['user_id'] == 'test-user'
        assert len(data['subscriptions']) == 0
        assert len(data['active_subscriptions']) == 0
        assert data['total_subscriptions'] == 0
        assert data['active_count'] == 0

    def test_get_user_subscriptions_invalid_user_id(self, client):
        """Test with invalid user ID format"""
        response = client.get('/api/users/invalid-user-id-format-123456789012345678901234567890/subscriptions')
        
        assert response.status_code == 400
        data = json.loads(response.data)
        assert data['error']['code'] == 'INVALID_USER_ID'

    def test_get_user_subscriptions_user_not_found(self, client):
        """Test with non-existent user"""
        response = client.get('/api/users/nonexistent/subscriptions')
        
        assert response.status_code == 404
        data = json.loads(response.data)
        assert data['error']['code'] == 'USER_NOT_FOUND'


class TestPurchaseSubscription:
    """Test POST /api/users/<user_id>/subscriptions/<subject>"""

    def test_purchase_subscription_monthly_success(self, client, sample_user):
        """Test successful monthly subscription purchase"""
        request_data = {
            'plan': 'monthly',
            'payment_method': 'mock'
        }
        
        response = client.post(
            '/api/users/test-user/subscriptions/python',
            data=json.dumps(request_data),
            content_type='application/json'
        )
        
        assert response.status_code == 201
        data = json.loads(response.data)
        
        assert 'Successfully purchased monthly subscription' in data['message']
        assert data['subscription']['user_id'] == 'test-user'
        assert data['subscription']['subject'] == 'python'
        assert data['subscription']['status'] == 'active'
        assert data['subject_info']['name'] == 'Python Programming'
        assert data['payment']['plan'] == 'monthly'
        assert data['payment']['amount'] == 29.99

    def test_purchase_subscription_yearly_success(self, client, sample_user):
        """Test successful yearly subscription purchase"""
        request_data = {
            'plan': 'yearly',
            'payment_method': 'mock'
        }
        
        response = client.post(
            '/api/users/test-user/subscriptions/python',
            data=json.dumps(request_data),
            content_type='application/json'
        )
        
        assert response.status_code == 201
        data = json.loads(response.data)
        
        assert 'Successfully purchased yearly subscription' in data['message']
        assert data['payment']['plan'] == 'yearly'
        assert data['payment']['amount'] == 299.99

    def test_purchase_subscription_default_monthly(self, client, sample_user):
        """Test subscription purchase defaults to monthly plan"""
        request_data = {
            'payment_method': 'mock'
        }
        
        response = client.post(
            '/api/users/test-user/subscriptions/python',
            data=json.dumps(request_data),
            content_type='application/json'
        )
        
        assert response.status_code == 201
        data = json.loads(response.data)
        assert data['payment']['plan'] == 'monthly'

    def test_purchase_subscription_existing_active(self, client, sample_user, sample_subscription):
        """Test purchase when user already has active subscription"""
        request_data = {
            'plan': 'monthly',
            'payment_method': 'mock'
        }
        
        response = client.post(
            '/api/users/test-user/subscriptions/python',
            data=json.dumps(request_data),
            content_type='application/json'
        )
        
        assert response.status_code == 409
        data = json.loads(response.data)
        assert data['error']['code'] == 'SUBSCRIPTION_EXISTS'

    def test_purchase_subscription_invalid_plan(self, client, sample_user):
        """Test purchase with invalid plan"""
        request_data = {
            'plan': 'invalid',
            'payment_method': 'mock'
        }
        
        response = client.post(
            '/api/users/test-user/subscriptions/python',
            data=json.dumps(request_data),
            content_type='application/json'
        )
        
        assert response.status_code == 400
        data = json.loads(response.data)
        assert data['error']['code'] == 'INVALID_PLAN'

    def test_purchase_subscription_invalid_subject(self, client, sample_user):
        """Test purchase with invalid subject"""
        request_data = {
            'plan': 'monthly',
            'payment_method': 'mock'
        }
        
        response = client.post(
            '/api/users/test-user/subscriptions/invalid-subject',
            data=json.dumps(request_data),
            content_type='application/json'
        )
        
        assert response.status_code == 404
        data = json.loads(response.data)
        assert data['error']['code'] == 'SUBJECT_NOT_FOUND'

    def test_purchase_subscription_user_not_found(self, client):
        """Test purchase with non-existent user"""
        request_data = {
            'plan': 'monthly',
            'payment_method': 'mock'
        }
        
        response = client.post(
            '/api/users/nonexistent/subscriptions/python',
            data=json.dumps(request_data),
            content_type='application/json'
        )
        
        assert response.status_code == 404
        data = json.loads(response.data)
        assert data['error']['code'] == 'USER_NOT_FOUND'

    def test_purchase_subscription_unsupported_payment_method(self, client, sample_user):
        """Test purchase with unsupported payment method"""
        request_data = {
            'plan': 'monthly',
            'payment_method': 'stripe'
        }
        
        response = client.post(
            '/api/users/test-user/subscriptions/python',
            data=json.dumps(request_data),
            content_type='application/json'
        )
        
        assert response.status_code == 400
        data = json.loads(response.data)
        assert data['error']['code'] == 'PAYMENT_METHOD_NOT_SUPPORTED'


class TestCancelSubscription:
    """Test DELETE /api/users/<user_id>/subscriptions/<subject>"""

    def test_cancel_subscription_success(self, client, sample_user, sample_subscription):
        """Test successful subscription cancellation"""
        response = client.delete('/api/users/test-user/subscriptions/python')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        
        assert 'Successfully cancelled subscription' in data['message']
        assert data['subscription']['status'] == 'cancelled'
        assert data['subject_info']['name'] == 'Python Programming'
        assert 'cancelled_at' in data

    def test_cancel_subscription_not_found(self, client, sample_user):
        """Test cancellation when subscription doesn't exist"""
        response = client.delete('/api/users/test-user/subscriptions/python')
        
        assert response.status_code == 404
        data = json.loads(response.data)
        assert data['error']['code'] == 'SUBSCRIPTION_NOT_FOUND'

    def test_cancel_subscription_already_cancelled(self, client, sample_user):
        """Test cancellation of already cancelled subscription"""
        # Create cancelled subscription
        with client.application.app_context():
            subscription = Subscription(
                user_id='test-user',
                subject='python',
                status='cancelled'
            )
            db.session.add(subscription)
            db.session.commit()
        
        response = client.delete('/api/users/test-user/subscriptions/python')
        
        assert response.status_code == 400
        data = json.loads(response.data)
        assert data['error']['code'] == 'SUBSCRIPTION_NOT_ACTIVE'

    def test_cancel_subscription_invalid_subject(self, client, sample_user):
        """Test cancellation with invalid subject"""
        response = client.delete('/api/users/test-user/subscriptions/invalid-subject')
        
        assert response.status_code == 404
        data = json.loads(response.data)
        assert data['error']['code'] == 'SUBJECT_NOT_FOUND'

    def test_cancel_subscription_user_not_found(self, client):
        """Test cancellation with non-existent user"""
        response = client.delete('/api/users/nonexistent/subscriptions/python')
        
        assert response.status_code == 404
        data = json.loads(response.data)
        assert data['error']['code'] == 'USER_NOT_FOUND'


class TestGetSubscriptionStatus:
    """Test GET /api/users/<user_id>/subscriptions/<subject>/status"""

    def test_get_subscription_status_active(self, client, sample_user, sample_subscription):
        """Test getting status for active subscription"""
        response = client.get('/api/users/test-user/subscriptions/python/status')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        
        assert data['user_id'] == 'test-user'
        assert data['subject']['id'] == 'python'
        assert data['subject']['name'] == 'Python Programming'
        assert data['subscription']['status'] == 'active'
        assert data['status']['has_active_subscription'] is True
        assert data['status']['can_access_content'] is True
        assert data['status']['requires_payment'] is False
        assert data['pricing']['monthly'] == 29.99
        assert data['pricing']['yearly'] == 299.99

    def test_get_subscription_status_no_subscription(self, client, sample_user):
        """Test getting status when no subscription exists"""
        response = client.get('/api/users/test-user/subscriptions/python/status')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        
        assert data['user_id'] == 'test-user'
        assert data['subscription'] is None
        assert data['status']['has_active_subscription'] is False
        assert data['status']['can_access_content'] is False
        assert data['status']['requires_payment'] is True

    def test_get_subscription_status_expired(self, client, sample_user):
        """Test getting status for expired subscription"""
        with client.application.app_context():
            subscription = Subscription(
                user_id='test-user',
                subject='python',
                status='active',
                expires_at=datetime.utcnow() - timedelta(days=1)  # Expired
            )
            db.session.add(subscription)
            db.session.commit()
        
        response = client.get('/api/users/test-user/subscriptions/python/status')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        
        assert data['status']['has_active_subscription'] is False
        assert data['status']['requires_payment'] is True

    def test_get_subscription_status_invalid_subject(self, client, sample_user):
        """Test getting status with invalid subject"""
        response = client.get('/api/users/test-user/subscriptions/invalid-subject/status')
        
        assert response.status_code == 404
        data = json.loads(response.data)
        assert data['error']['code'] == 'SUBJECT_NOT_FOUND'

    def test_get_subscription_status_user_not_found(self, client):
        """Test getting status with non-existent user"""
        response = client.get('/api/users/nonexistent/subscriptions/python/status')
        
        assert response.status_code == 404
        data = json.loads(response.data)
        assert data['error']['code'] == 'USER_NOT_FOUND'


class TestSubscriptionIntegration:
    """Integration tests for subscription workflows"""

    def test_complete_subscription_lifecycle(self, client, sample_user):
        """Test complete subscription purchase and cancellation lifecycle"""
        # 1. Check initial status (no subscription)
        response = client.get('/api/users/test-user/subscriptions/python/status')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['status']['has_active_subscription'] is False
        
        # 2. Purchase subscription
        request_data = {
            'plan': 'monthly',
            'payment_method': 'mock'
        }
        response = client.post(
            '/api/users/test-user/subscriptions/python',
            data=json.dumps(request_data),
            content_type='application/json'
        )
        assert response.status_code == 201
        
        # 3. Check status after purchase (active)
        response = client.get('/api/users/test-user/subscriptions/python/status')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['status']['has_active_subscription'] is True
        
        # 4. Get all user subscriptions
        response = client.get('/api/users/test-user/subscriptions')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['active_count'] == 1
        
        # 5. Cancel subscription
        response = client.delete('/api/users/test-user/subscriptions/python')
        assert response.status_code == 200
        
        # 6. Check status after cancellation (inactive)
        response = client.get('/api/users/test-user/subscriptions/python/status')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['status']['has_active_subscription'] is False

    def test_multiple_subjects_subscription(self, client, sample_user):
        """Test subscribing to multiple subjects"""
        subjects = ['python', 'javascript', 'react']
        
        # Purchase subscriptions for multiple subjects
        for subject in subjects:
            request_data = {
                'plan': 'monthly',
                'payment_method': 'mock'
            }
            response = client.post(
                f'/api/users/test-user/subscriptions/{subject}',
                data=json.dumps(request_data),
                content_type='application/json'
            )
            assert response.status_code == 201
        
        # Check that all subscriptions are active
        response = client.get('/api/users/test-user/subscriptions')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['active_count'] == 3
        assert data['total_subscriptions'] == 3
        
        # Verify each subject has active subscription
        for subject in subjects:
            response = client.get(f'/api/users/test-user/subscriptions/{subject}/status')
            assert response.status_code == 200
            data = json.loads(response.data)
            assert data['status']['has_active_subscription'] is True

    def test_subscription_renewal_workflow(self, client, sample_user):
        """Test subscription renewal by purchasing again"""
        # Purchase initial subscription
        request_data = {
            'plan': 'monthly',
            'payment_method': 'mock'
        }
        response = client.post(
            '/api/users/test-user/subscriptions/python',
            data=json.dumps(request_data),
            content_type='application/json'
        )
        assert response.status_code == 201
        
        # Try to purchase again (should conflict)
        response = client.post(
            '/api/users/test-user/subscriptions/python',
            data=json.dumps(request_data),
            content_type='application/json'
        )
        assert response.status_code == 409
        
        # Cancel subscription
        response = client.delete('/api/users/test-user/subscriptions/python')
        assert response.status_code == 200
        
        # Purchase again after cancellation (should work)
        response = client.post(
            '/api/users/test-user/subscriptions/python',
            data=json.dumps(request_data),
            content_type='application/json'
        )
        assert response.status_code == 201