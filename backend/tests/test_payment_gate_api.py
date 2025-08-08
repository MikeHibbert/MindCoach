"""
Integration tests for payment gate API endpoints
"""

import unittest
import json
from datetime import datetime, timedelta
from app import create_app, db
from app.models.user import User
from app.models.subscription import Subscription


class TestPaymentGateAccessCheck(unittest.TestCase):
    """Test payment gate access check endpoint"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.app = create_app('testing')
        self.client = self.app.test_client()
        
        with self.app.app_context():
            db.create_all()
            
            # Create test user
            self.test_user = User(user_id='test_user_123', email='test@example.com')
            db.session.add(self.test_user)
            
            # Create test user with subscription
            self.test_user_with_sub = User(user_id='test_user_with_sub', email='test_with_sub@example.com')
            db.session.add(self.test_user_with_sub)
            
            subscription = Subscription(
                user_id=self.test_user_with_sub.user_id,
                subject='python',
                status='active',
                expires_at=datetime.utcnow() + timedelta(days=30)
            )
            db.session.add(subscription)
            db.session.commit()
    
    def tearDown(self):
        """Clean up after tests"""
        with self.app.app_context():
            db.drop_all()
    
    def test_access_check_with_subscription(self):
        """Test access check with active subscription"""
        response = self.client.get(f'/api/users/{self.test_user_with_sub.user_id}/subjects/python/access-check')
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertTrue(data['access_granted'])
        self.assertEqual(data['reason'], 'ACCESS_GRANTED')
    
    def test_access_check_without_subscription(self):
        """Test access check without subscription"""
        response = self.client.get(f'/api/users/{self.test_user.user_id}/subjects/python/access-check')
        
        self.assertEqual(response.status_code, 402)
        data = json.loads(response.data)
        self.assertFalse(data['access_granted'])
        self.assertEqual(data['reason'], 'SUBSCRIPTION_REQUIRED')
        self.assertIn('pricing', data['details'])
    
    def test_access_check_invalid_user(self):
        """Test access check with invalid user"""
        response = self.client.get('/api/users/invalid@user/subjects/python/access-check')
        
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.data)
        self.assertEqual(data['error']['code'], 'INVALID_USER_ID')
    
    def test_access_check_invalid_subject(self):
        """Test access check with invalid subject"""
        response = self.client.get(f'/api/users/{self.test_user.user_id}/subjects/invalid@subject/access-check')
        
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.data)
        self.assertEqual(data['error']['code'], 'INVALID_SUBJECT')
    
    def test_access_check_nonexistent_user(self):
        """Test access check with nonexistent user"""
        response = self.client.get('/api/users/nonexistent_user/subjects/python/access-check')
        
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.data)
        self.assertEqual(data['reason'], 'USER_NOT_FOUND')


class TestPurchaseInitiation(unittest.TestCase):
    """Test purchase initiation endpoint"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.app = create_app('testing')
        self.client = self.app.test_client()
        
        with self.app.app_context():
            db.create_all()
            
            # Create test user
            self.test_user = User(user_id='test_user_123', email='test@example.com')
            db.session.add(self.test_user)
            
            # Create test user with subscription
            self.test_user_with_sub = User(user_id='test_user_with_sub', email='test_with_sub@example.com')
            db.session.add(self.test_user_with_sub)
            
            subscription = Subscription(
                user_id=self.test_user_with_sub.user_id,
                subject='python',
                status='active',
                expires_at=datetime.utcnow() + timedelta(days=30)
            )
            db.session.add(subscription)
            db.session.commit()
    
    def tearDown(self):
        """Clean up after tests"""
        with self.app.app_context():
            db.drop_all()
    
    def test_initiate_purchase_monthly(self):
        """Test initiating monthly subscription purchase"""
        response = self.client.post(
            f'/api/users/{self.test_user.user_id}/subjects/python/purchase/initiate',
            json={'subscription_type': 'monthly'}
        )
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertIn('purchase_data', data)
        self.assertEqual(data['purchase_data']['subscription_type'], 'monthly')
        self.assertEqual(data['purchase_data']['amount'], 29.99)
        self.assertEqual(data['next_step'], 'PROCESS_PAYMENT')
    
    def test_initiate_purchase_yearly(self):
        """Test initiating yearly subscription purchase"""
        response = self.client.post(
            f'/api/users/{self.test_user.user_id}/subjects/python/purchase/initiate',
            json={'subscription_type': 'yearly'}
        )
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertEqual(data['purchase_data']['subscription_type'], 'yearly')
        self.assertEqual(data['purchase_data']['amount'], 299.99)
    
    def test_initiate_purchase_default_monthly(self):
        """Test initiating purchase defaults to monthly"""
        response = self.client.post(
            f'/api/users/{self.test_user.user_id}/subjects/python/purchase/initiate',
            json={}
        )
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertEqual(data['purchase_data']['subscription_type'], 'monthly')
    
    def test_initiate_purchase_existing_subscription(self):
        """Test initiating purchase with existing subscription"""
        response = self.client.post(
            f'/api/users/{self.test_user_with_sub.user_id}/subjects/python/purchase/initiate',
            json={'subscription_type': 'monthly'}
        )
        
        self.assertEqual(response.status_code, 409)
        data = json.loads(response.data)
        self.assertEqual(data['error'], 'SUBSCRIPTION_EXISTS')


class TestPurchaseCompletion(unittest.TestCase):
    """Test purchase completion endpoint"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.app = create_app('testing')
        self.client = self.app.test_client()
        
        with self.app.app_context():
            db.create_all()
            
            # Create test user
            self.test_user = User(user_id='test_user_123', email='test@example.com')
            db.session.add(self.test_user)
            db.session.commit()
    
    def tearDown(self):
        """Clean up after tests"""
        with self.app.app_context():
            db.drop_all()
    
    def test_complete_purchase_monthly(self):
        """Test completing monthly subscription purchase"""
        response = self.client.post(
            f'/api/users/{self.test_user.user_id}/subjects/python/purchase/complete',
            json={
                'subscription_type': 'monthly',
                'payment_reference': 'payment_123',
                'payment_amount': 29.99
            }
        )
        
        self.assertEqual(response.status_code, 201)
        data = json.loads(response.data)
        self.assertIn('subscription', data)
        self.assertEqual(data['subscription']['status'], 'active')
        self.assertEqual(data['subscription']['subject'], 'python')
        self.assertEqual(data['payment_reference'], 'payment_123')
    
    def test_complete_purchase_yearly(self):
        """Test completing yearly subscription purchase"""
        response = self.client.post(
            f'/api/users/{self.test_user.user_id}/subjects/javascript/purchase/complete',
            json={
                'subscription_type': 'yearly',
                'payment_reference': 'payment_456',
                'payment_amount': 299.99
            }
        )
        
        self.assertEqual(response.status_code, 201)
        data = json.loads(response.data)
        self.assertEqual(data['subscription']['subject'], 'javascript')
        self.assertIn('Successfully purchased yearly subscription', data['message'])
    
    def test_complete_purchase_invalid_amount(self):
        """Test completing purchase with invalid payment amount"""
        response = self.client.post(
            f'/api/users/{self.test_user.user_id}/subjects/python/purchase/complete',
            json={
                'subscription_type': 'monthly',
                'payment_reference': 'payment_123',
                'payment_amount': 25.00  # Wrong amount
            }
        )
        
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.data)
        self.assertEqual(data['error'], 'INVALID_PAYMENT_AMOUNT')
        self.assertEqual(data['expected_amount'], 29.99)


class TestPaymentGateWorkflowIntegration(unittest.TestCase):
    """Test complete payment gate workflow integration"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.app = create_app('testing')
        self.client = self.app.test_client()
        
        with self.app.app_context():
            db.create_all()
            
            # Create test user
            self.test_user = User(user_id='test_user_123', email='test@example.com')
            db.session.add(self.test_user)
            db.session.commit()
    
    def tearDown(self):
        """Clean up after tests"""
        with self.app.app_context():
            db.drop_all()
    
    def test_complete_purchase_workflow(self):
        """Test complete purchase workflow from initiation to completion"""
        # Step 1: Check initial access (should be denied)
        response = self.client.get(f'/api/users/{self.test_user.user_id}/subjects/python/access-check')
        self.assertEqual(response.status_code, 402)
        
        # Step 2: Initiate purchase
        response = self.client.post(
            f'/api/users/{self.test_user.user_id}/subjects/python/purchase/initiate',
            json={'subscription_type': 'monthly'}
        )
        self.assertEqual(response.status_code, 200)
        purchase_data = json.loads(response.data)['purchase_data']
        
        # Step 3: Complete purchase
        response = self.client.post(
            f'/api/users/{self.test_user.user_id}/subjects/python/purchase/complete',
            json={
                'subscription_type': 'monthly',
                'payment_reference': 'payment_123',
                'payment_amount': purchase_data['amount']
            }
        )
        self.assertEqual(response.status_code, 201)
        
        # Step 4: Check access again (should be granted)
        response = self.client.get(f'/api/users/{self.test_user.user_id}/subjects/python/access-check')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertTrue(data['access_granted'])
        
        # Step 5: Verify payment summary
        response = self.client.get(f'/api/users/{self.test_user.user_id}/payment-summary')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertEqual(data['active_subscriptions'], 1)
    
    def test_subscription_renewal_workflow(self):
        """Test subscription renewal workflow"""
        with self.app.app_context():
            # Create expired subscription
            expired_sub = Subscription(
                user_id=self.test_user.user_id,
                subject='python',
                status='active',
                expires_at=datetime.utcnow() - timedelta(days=1)
            )
            db.session.add(expired_sub)
            db.session.commit()
        
        # Check access is denied due to expiration
        response = self.client.get(f'/api/users/{self.test_user.user_id}/subjects/python/access-check')
        self.assertEqual(response.status_code, 402)
        
        # Renew subscription by completing purchase
        response = self.client.post(
            f'/api/users/{self.test_user.user_id}/subjects/python/purchase/complete',
            json={
                'subscription_type': 'monthly',
                'payment_reference': 'renewal_123'
            }
        )
        self.assertEqual(response.status_code, 201)
        
        # Check access is now granted
        response = self.client.get(f'/api/users/{self.test_user.user_id}/subjects/python/access-check')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertTrue(data['access_granted'])
    
    def test_multiple_subject_purchase_workflow(self):
        """Test purchasing multiple subjects"""
        subjects = ['python', 'javascript', 'react']
        
        for subject in subjects:
            # Complete purchase for each subject
            response = self.client.post(
                f'/api/users/{self.test_user.user_id}/subjects/{subject}/purchase/complete',
                json={
                    'subscription_type': 'monthly',
                    'payment_reference': f'payment_{subject}'
                }
            )
            self.assertEqual(response.status_code, 201)
            
            # Verify access is granted
            response = self.client.get(f'/api/users/{self.test_user.user_id}/subjects/{subject}/access-check')
            self.assertEqual(response.status_code, 200)
            data = json.loads(response.data)
            self.assertTrue(data['access_granted'])
        
        # Check payment summary
        response = self.client.get(f'/api/users/{self.test_user.user_id}/payment-summary')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertEqual(data['active_subscriptions'], 3)
        self.assertEqual(data['total_subscriptions'], 3)


class TestSubjectPricing(unittest.TestCase):
    """Test subject pricing endpoint"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.app = create_app('testing')
        self.client = self.app.test_client()
        
        with self.app.app_context():
            db.create_all()
    
    def tearDown(self):
        """Clean up after tests"""
        with self.app.app_context():
            db.drop_all()
    
    def test_get_subject_pricing(self):
        """Test getting pricing for valid subject"""
        response = self.client.get('/api/subjects/python/pricing')
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertEqual(data['subject'], 'python')
        self.assertIn('pricing', data)
        self.assertEqual(data['pricing']['monthly'], 29.99)
        self.assertEqual(data['pricing']['yearly'], 299.99)
    
    def test_get_subject_pricing_all_subjects(self):
        """Test getting pricing for all available subjects"""
        subjects = ['python', 'javascript', 'react', 'nodejs', 'sql']
        
        for subject in subjects:
            response = self.client.get(f'/api/subjects/{subject}/pricing')
            self.assertEqual(response.status_code, 200)
            data = json.loads(response.data)
            self.assertEqual(data['subject'], subject)
            self.assertIn('monthly', data['pricing'])
            self.assertIn('yearly', data['pricing'])
    
    def test_get_subject_pricing_invalid_subject(self):
        """Test getting pricing for invalid subject"""
        response = self.client.get('/api/subjects/invalid@subject/pricing')
        
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.data)
        self.assertEqual(data['error']['code'], 'INVALID_SUBJECT')
    
    def test_get_subject_pricing_nonexistent_subject(self):
        """Test getting pricing for nonexistent subject"""
        response = self.client.get('/api/subjects/nonexistent/pricing')
        
        self.assertEqual(response.status_code, 404)
        data = json.loads(response.data)
        self.assertEqual(data['error']['code'], 'SUBJECT_NOT_FOUND')


class TestExpiredSubscriptionProcessing(unittest.TestCase):
    """Test expired subscription processing endpoint"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.app = create_app('testing')
        self.client = self.app.test_client()
        
        with self.app.app_context():
            db.create_all()
            
            # Create test user
            self.test_user = User(user_id='test_user_123', email='test@example.com')
            db.session.add(self.test_user)
            db.session.commit()
    
    def tearDown(self):
        """Clean up after tests"""
        with self.app.app_context():
            db.drop_all()
    
    def test_process_expired_subscriptions(self):
        """Test processing expired subscriptions"""
        with self.app.app_context():
            # Create expired subscription
            expired_sub = Subscription(
                user_id=self.test_user.user_id,
                subject='python',
                status='active',
                expires_at=datetime.utcnow() - timedelta(days=1)
            )
            db.session.add(expired_sub)
            
            # Create active subscription
            active_sub = Subscription(
                user_id=self.test_user.user_id,
                subject='javascript',
                status='active',
                expires_at=datetime.utcnow() + timedelta(days=30)
            )
            db.session.add(active_sub)
            db.session.commit()
        
        response = self.client.post('/api/admin/subscriptions/expired/process')
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertEqual(data['processed_count'], 1)
        self.assertEqual(len(data['expired_subscriptions']), 1)
        self.assertEqual(data['expired_subscriptions'][0]['subject'], 'python')
        self.assertIn('Processed 1 expired subscriptions', data['message'])
    
    def test_process_expired_subscriptions_none_expired(self):
        """Test processing when no subscriptions are expired"""
        with self.app.app_context():
            # Create only active subscription
            active_sub = Subscription(
                user_id=self.test_user.user_id,
                subject='python',
                status='active',
                expires_at=datetime.utcnow() + timedelta(days=30)
            )
            db.session.add(active_sub)
            db.session.commit()
        
        response = self.client.post('/api/admin/subscriptions/expired/process')
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertEqual(data['processed_count'], 0)
        self.assertEqual(len(data['expired_subscriptions']), 0)


if __name__ == '__main__':
    unittest.main()