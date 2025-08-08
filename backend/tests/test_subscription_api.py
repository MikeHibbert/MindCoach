"""
Tests for subscription management API endpoints
"""

import pytest
import json
from datetime import datetime, timedelta
from app import create_app, db
from app.models.user import User
from app.models.subscription import Subscription


@pytest.fixture
def app():
    """Create test app"""
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
def test_user(app):
    """Create test user"""
    with app.app_context():
        user = User(user_id='test_user_123', email='test@example.com')
        db.session.add(user)
        db.session.commit()
        return user


@pytest.fixture
def test_subscription(app, test_user):
    """Create test subscription"""
    with app.app_context():
        subscription = Subscription(
            user_id=test_user.user_id,
            subject='python',
            status='active',
            expires_at=datetime.utcnow() + timedelta(days=30)
        )
        db.session.add(subscription)
        db.session.commit()
        return subscription


class TestListSubscriptions:
    """Test subscription listing endpoint"""
    
    def test_list_subscriptions_success(self, client, test_user, test_subscription):
        """Test successful subscription listing"""
        response = client.get(f'/api/users/{test_user.user_id}/subscriptions')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert 'subscriptions' in data
        assert len(data['subscriptions']) == 1
        assert data['subscriptions'][0]['subject'] == 'python'
        assert data['subscriptions'][0]['status'] == 'active'
    
    def test_list_subscriptions_empty(self, client, test_user):
        """Test listing subscriptions for user with no subscriptions"""
        response = client.get(f'/api/users/{test_user.user_id}/subscriptions')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert 'subscriptions' in data
        assert len(data['subscriptions']) == 0
    
    def test_list_subscriptions_invalid_user_id(self, client):
        """Test listing subscriptions with invalid user ID"""
        response = client.get('/api/users/invalid@user/subscriptions')
        
        assert response.status_code == 400
        data = json.loads(response.data)
        assert data['error']['code'] == 'INVALID_USER_ID'
    
    def test_list_subscriptions_user_not_found(self, client):
        """Test listing subscriptions for non-existent user"""
        response = client.get('/api/users/nonexistent_user/subscriptions')
        
        assert response.status_code == 404
        data = json.loads(response.data)
        assert data['error']['code'] == 'USER_NOT_FOUND'


class TestPurchaseSubscription:
    """Test subscription purchase endpoint"""
    
    def test_purchase_subscription_success_monthly(self, client, test_user):
        """Test successful monthly subscription purchase"""
        response = client.post(
            f'/api/users/{test_user.user_id}/subscriptions/python',
            json={'type': 'monthly'}
        )
        
        assert response.status_code == 201
        data = json.loads(response.data)
        assert 'subscription' in data
        assert data['subscription']['subject'] == 'python'
        assert data['subscription']['status'] == 'active'
        assert 'Successfully purchased monthly subscription' in data['message']
    
    def test_purchase_subscription_success_yearly(self, client, test_user):
        """Test successful yearly subscription purchase"""
        response = client.post(
            f'/api/users/{test_user.user_id}/subscriptions/javascript',
            json={'type': 'yearly'}
        )
        
        assert response.status_code == 201
        data = json.loads(response.data)
        assert 'subscription' in data
        assert data['subscription']['subject'] == 'javascript'
        assert data['subscription']['status'] == 'active'
        assert 'Successfully purchased yearly subscription' in data['message']
    
    def test_purchase_subscription_default_monthly(self, client, test_user):
        """Test subscription purchase defaults to monthly"""
        response = client.post(
            f'/api/users/{test_user.user_id}/subscriptions/python',
            json={}
        )
        
        assert response.status_code == 201
        data = json.loads(response.data)
        assert 'subscription' in data
        assert data['subscription']['subject'] == 'python'
        assert 'Successfully purchased monthly subscription' in data['message']
    
    def test_purchase_subscription_already_exists(self, client, test_user, test_subscription):
        """Test purchasing subscription that already exists"""
        response = client.post(
            f'/api/users/{test_user.user_id}/subscriptions/python',
            json={'type': 'monthly'}
        )
        
        assert response.status_code == 409
        data = json.loads(response.data)
        assert data['error']['code'] == 'SUBSCRIPTION_EXISTS'
    
    def test_purchase_subscription_invalid_user_id(self, client):
        """Test purchasing subscription with invalid user ID"""
        response = client.post(
            '/api/users/invalid@user/subscriptions/python',
            json={'type': 'monthly'}
        )
        
        assert response.status_code == 400
        data = json.loads(response.data)
        assert data['error']['code'] == 'INVALID_USER_ID'
    
    def test_purchase_subscription_invalid_subject(self, client, test_user):
        """Test purchasing subscription with invalid subject"""
        response = client.post(
            f'/api/users/{test_user.user_id}/subscriptions/Invalid@Subject',
            json={'type': 'monthly'}
        )
        
        assert response.status_code == 400
        data = json.loads(response.data)
        assert data['error']['code'] == 'INVALID_SUBJECT'
    
    def test_purchase_subscription_user_not_found(self, client):
        """Test purchasing subscription for non-existent user"""
        response = client.post(
            '/api/users/nonexistent_user/subscriptions/python',
            json={'type': 'monthly'}
        )
        
        assert response.status_code == 404
        data = json.loads(response.data)
        assert data['error']['code'] == 'USER_NOT_FOUND'


class TestCancelSubscription:
    """Test subscription cancellation endpoint"""
    
    def test_cancel_subscription_success(self, client, test_user, test_subscription):
        """Test successful subscription cancellation"""
        response = client.delete(f'/api/users/{test_user.user_id}/subscriptions/python')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert 'subscription' in data
        assert data['subscription']['status'] == 'cancelled'
        assert 'Successfully cancelled subscription' in data['message']
    
    def test_cancel_subscription_not_found(self, client, test_user):
        """Test cancelling non-existent subscription"""
        response = client.delete(f'/api/users/{test_user.user_id}/subscriptions/nonexistent')
        
        assert response.status_code == 404
        data = json.loads(response.data)
        assert data['error']['code'] == 'SUBSCRIPTION_NOT_FOUND'
    
    def test_cancel_subscription_invalid_user_id(self, client):
        """Test cancelling subscription with invalid user ID"""
        response = client.delete('/api/users/invalid@user/subscriptions/python')
        
        assert response.status_code == 400
        data = json.loads(response.data)
        assert data['error']['code'] == 'INVALID_USER_ID'
    
    def test_cancel_subscription_invalid_subject(self, client, test_user):
        """Test cancelling subscription with invalid subject"""
        response = client.delete(f'/api/users/{test_user.user_id}/subscriptions/Invalid@Subject')
        
        assert response.status_code == 400
        data = json.loads(response.data)
        assert data['error']['code'] == 'INVALID_SUBJECT'
    
    def test_cancel_subscription_user_not_found(self, client):
        """Test cancelling subscription for non-existent user"""
        response = client.delete('/api/users/nonexistent_user/subscriptions/python')
        
        assert response.status_code == 404
        data = json.loads(response.data)
        assert data['error']['code'] == 'USER_NOT_FOUND'


class TestCheckSubscriptionStatus:
    """Test subscription status checking endpoint"""
    
    def test_check_subscription_status_active(self, client, test_user, test_subscription):
        """Test checking status of active subscription"""
        response = client.get(f'/api/users/{test_user.user_id}/subscriptions/python/status')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['user_id'] == test_user.user_id
        assert data['subject'] == 'python'
        assert data['has_active_subscription'] is True
        assert data['subscription'] is not None
        assert data['subscription']['status'] == 'active'
    
    def test_check_subscription_status_no_subscription(self, client, test_user):
        """Test checking status when no subscription exists"""
        response = client.get(f'/api/users/{test_user.user_id}/subscriptions/javascript/status')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['user_id'] == test_user.user_id
        assert data['subject'] == 'javascript'
        assert data['has_active_subscription'] is False
        assert data['subscription'] is None
    
    def test_check_subscription_status_expired(self, client, test_user, app):
        """Test checking status of expired subscription"""
        with app.app_context():
            # Create expired subscription
            expired_subscription = Subscription(
                user_id=test_user.user_id,
                subject='python',
                status='active',
                expires_at=datetime.utcnow() - timedelta(days=1)
            )
            db.session.add(expired_subscription)
            db.session.commit()
        
        response = client.get(f'/api/users/{test_user.user_id}/subscriptions/python/status')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['has_active_subscription'] is False
        assert data['subscription']['status'] == 'active'  # Status is active but expired
    
    def test_check_subscription_status_invalid_user_id(self, client):
        """Test checking subscription status with invalid user ID"""
        response = client.get('/api/users/invalid@user/subscriptions/python/status')
        
        assert response.status_code == 400
        data = json.loads(response.data)
        assert data['error']['code'] == 'INVALID_USER_ID'
    
    def test_check_subscription_status_invalid_subject(self, client, test_user):
        """Test checking subscription status with invalid subject"""
        response = client.get(f'/api/users/{test_user.user_id}/subscriptions/Invalid@Subject/status')
        
        assert response.status_code == 400
        data = json.loads(response.data)
        assert data['error']['code'] == 'INVALID_SUBJECT'
    
    def test_check_subscription_status_user_not_found(self, client):
        """Test checking subscription status for non-existent user"""
        response = client.get('/api/users/nonexistent_user/subscriptions/python/status')
        
        assert response.status_code == 404
        data = json.loads(response.data)
        assert data['error']['code'] == 'USER_NOT_FOUND'


class TestListActiveSubscriptions:
    """Test active subscriptions listing endpoint"""
    
    def test_list_active_subscriptions_success(self, client, test_user, test_subscription, app):
        """Test successful active subscriptions listing"""
        with app.app_context():
            # Add another active subscription
            subscription2 = Subscription(
                user_id=test_user.user_id,
                subject='javascript',
                status='active',
                expires_at=datetime.utcnow() + timedelta(days=60)
            )
            db.session.add(subscription2)
            db.session.commit()
        
        response = client.get(f'/api/users/{test_user.user_id}/subscriptions/active')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert 'active_subscriptions' in data
        assert data['count'] == 2
        subjects = [sub['subject'] for sub in data['active_subscriptions']]
        assert 'python' in subjects
        assert 'javascript' in subjects
    
    def test_list_active_subscriptions_excludes_expired(self, client, test_user, test_subscription, app):
        """Test that expired subscriptions are excluded"""
        with app.app_context():
            # Add expired subscription
            expired_subscription = Subscription(
                user_id=test_user.user_id,
                subject='javascript',
                status='active',
                expires_at=datetime.utcnow() - timedelta(days=1)
            )
            db.session.add(expired_subscription)
            db.session.commit()
        
        response = client.get(f'/api/users/{test_user.user_id}/subscriptions/active')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['count'] == 1  # Only the non-expired subscription
        assert data['active_subscriptions'][0]['subject'] == 'python'
    
    def test_list_active_subscriptions_excludes_cancelled(self, client, test_user, app):
        """Test that cancelled subscriptions are excluded"""
        with app.app_context():
            # Add cancelled subscription
            cancelled_subscription = Subscription(
                user_id=test_user.user_id,
                subject='python',
                status='cancelled',
                expires_at=datetime.utcnow() + timedelta(days=30)
            )
            db.session.add(cancelled_subscription)
            db.session.commit()
        
        response = client.get(f'/api/users/{test_user.user_id}/subscriptions/active')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['count'] == 0  # No active subscriptions
    
    def test_list_active_subscriptions_empty(self, client, test_user):
        """Test listing active subscriptions when none exist"""
        response = client.get(f'/api/users/{test_user.user_id}/subscriptions/active')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['count'] == 0
        assert len(data['active_subscriptions']) == 0
    
    def test_list_active_subscriptions_invalid_user_id(self, client):
        """Test listing active subscriptions with invalid user ID"""
        response = client.get('/api/users/invalid@user/subscriptions/active')
        
        assert response.status_code == 400
        data = json.loads(response.data)
        assert data['error']['code'] == 'INVALID_USER_ID'
    
    def test_list_active_subscriptions_user_not_found(self, client):
        """Test listing active subscriptions for non-existent user"""
        response = client.get('/api/users/nonexistent_user/subscriptions/active')
        
        assert response.status_code == 404
        data = json.loads(response.data)
        assert data['error']['code'] == 'USER_NOT_FOUND'


class TestSubscriptionBusinessLogic:
    """Test subscription business logic and validation"""
    
    def test_subscription_expiration_logic(self, client, test_user):
        """Test that subscription expiration is calculated correctly"""
        # Test monthly subscription
        response = client.post(
            f'/api/users/{test_user.user_id}/subscriptions/python',
            json={'type': 'monthly'}
        )
        
        assert response.status_code == 201
        data = json.loads(response.data)
        expires_at = datetime.fromisoformat(data['subscription']['expires_at'].replace('Z', '+00:00'))
        purchased_at = datetime.fromisoformat(data['subscription']['purchased_at'].replace('Z', '+00:00'))
        
        # Should be approximately 30 days
        duration = expires_at - purchased_at
        assert 29 <= duration.days <= 31
        
        # Test yearly subscription
        response = client.post(
            f'/api/users/{test_user.user_id}/subscriptions/javascript',
            json={'type': 'yearly'}
        )
        
        assert response.status_code == 201
        data = json.loads(response.data)
        expires_at = datetime.fromisoformat(data['subscription']['expires_at'].replace('Z', '+00:00'))
        purchased_at = datetime.fromisoformat(data['subscription']['purchased_at'].replace('Z', '+00:00'))
        
        # Should be approximately 365 days
        duration = expires_at - purchased_at
        assert 364 <= duration.days <= 366
    
    def test_subscription_renewal_logic(self, client, test_user, app):
        """Test that expired subscriptions can be renewed"""
        with app.app_context():
            # Create expired subscription
            expired_subscription = Subscription(
                user_id=test_user.user_id,
                subject='python',
                status='active',
                expires_at=datetime.utcnow() - timedelta(days=1)
            )
            db.session.add(expired_subscription)
            db.session.commit()
        
        # Purchase new subscription (should renew the expired one)
        response = client.post(
            f'/api/users/{test_user.user_id}/subscriptions/python',
            json={'type': 'monthly'}
        )
        
        assert response.status_code == 201
        data = json.loads(response.data)
        
        # Check that subscription is now active and not expired
        expires_at = datetime.fromisoformat(data['subscription']['expires_at'].replace('Z', '+00:00'))
        assert expires_at > datetime.utcnow()
        assert data['subscription']['status'] == 'active'