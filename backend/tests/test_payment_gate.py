"""
Integration tests for payment gate functionality
"""

import unittest
import json
import time
from datetime import datetime, timedelta
from app import create_app, db
from app.models.user import User
from app.models.subscription import Subscription
from app.services.payment_gate_service import PaymentGateService


class TestSubjectAccessControl(unittest.TestCase):
    """Test subject access control (payment gate)"""
    
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
    
    def test_list_subjects_without_user(self):
        """Test listing subjects without user context"""
        response = self.client.get('/api/subjects')
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertIn('subjects', data)
        self.assertGreater(len(data['subjects']), 0)
        
        # All subjects should be locked by default
        for subject in data['subjects']:
            self.assertTrue(subject['locked'])
            self.assertIn('pricing', subject)
    
    def test_list_subjects_with_user(self):
        """Test listing subjects with user context"""
        response = self.client.get(f'/api/subjects?user_id={self.test_user_with_sub.user_id}')
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertIn('subjects', data)
        
        # Find the python subject (user has subscription)
        python_subject = next((s for s in data['subjects'] if s['id'] == 'python'), None)
        self.assertIsNotNone(python_subject)
        self.assertFalse(python_subject['locked'])  # Should be unlocked
        
        # Other subjects should still be locked
        other_subjects = [s for s in data['subjects'] if s['id'] != 'python']
        for subject in other_subjects:
            self.assertTrue(subject['locked'])
    
    def test_subject_selection_with_active_subscription(self):
        """Test selecting subject with active subscription"""
        response = self.client.post(f'/api/users/{self.test_user_with_sub.user_id}/subjects/python/select')
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertIn('Successfully selected', data['message'])
        self.assertEqual(data['subject']['id'], 'python')
    
    def test_subject_selection_without_subscription(self):
        """Test selecting subject without subscription (payment gate)"""
        response = self.client.post(f'/api/users/{self.test_user.user_id}/subjects/python/select')
        
        self.assertEqual(response.status_code, 402)  # Payment Required
        data = json.loads(response.data)
        self.assertEqual(data['error']['code'], 'SUBSCRIPTION_REQUIRED')
        self.assertIn('pricing', data['error']['details'])
        self.assertEqual(data['error']['details']['subject'], 'python')
    
    def test_subject_access_check_with_subscription(self):
        """Test subject access check with active subscription"""
        response = self.client.get(f'/api/users/{self.test_user_with_sub.user_id}/subjects/python/access')
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertTrue(data['access_granted'])
        self.assertEqual(data['subject']['id'], 'python')
        self.assertIn('subscription_expires', data)
    
    def test_subject_access_check_without_subscription(self):
        """Test subject access check without subscription"""
        response = self.client.get(f'/api/users/{self.test_user.user_id}/subjects/python/access')
        
        self.assertEqual(response.status_code, 402)  # Payment Required
        data = json.loads(response.data)
        self.assertFalse(data['access_granted'])
        self.assertEqual(data['reason'], 'SUBSCRIPTION_REQUIRED')
        self.assertIn('subscription_options', data)
    
    def test_subject_status_check(self):
        """Test subject status check"""
        response = self.client.get(f'/api/users/{self.test_user_with_sub.user_id}/subjects/python/status')
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertTrue(data['access_status']['has_active_subscription'])
        self.assertFalse(data['access_status']['requires_payment'])
        self.assertIsNotNone(data['subscription'])


class TestSubscriptionPurchaseWorkflow(unittest.TestCase):
    """Test subscription purchase workflow"""
    
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
    
    def test_payment_gate_check_subject_access(self):
        """Test PaymentGateService.check_subject_access method"""
        with self.app.app_context():
            # Test without subscription
            has_access, reason, details = PaymentGateService.check_subject_access(self.test_user.user_id, 'python')
            self.assertFalse(has_access)
            self.assertEqual(reason, 'SUBSCRIPTION_REQUIRED')
            self.assertIn('pricing', details)
            
            # Create subscription and test again
            from app.services.subscription_service import SubscriptionService
            SubscriptionService.create_subscription(
                self.test_user.user_id, 'python', 'active',
                expires_at=datetime.utcnow() + timedelta(days=30)
            )
            
            has_access, reason, details = PaymentGateService.check_subject_access(self.test_user.user_id, 'python')
            self.assertTrue(has_access)
            self.assertEqual(reason, 'ACCESS_GRANTED')
    
    def test_initiate_subscription_purchase(self):
        """Test initiating subscription purchase"""
        with self.app.app_context():
            # Test monthly subscription
            success, result = PaymentGateService.initiate_subscription_purchase(
                self.test_user.user_id, 'python', 'monthly'
            )
            
            self.assertTrue(success)
            self.assertIn('purchase_data', result)
            self.assertEqual(result['purchase_data']['user_id'], self.test_user.user_id)
            self.assertEqual(result['purchase_data']['subject'], 'python')
            self.assertEqual(result['purchase_data']['subscription_type'], 'monthly')
            self.assertEqual(result['purchase_data']['amount'], 29.99)
            self.assertEqual(result['next_step'], 'PROCESS_PAYMENT')
            
            # Test yearly subscription
            success, result = PaymentGateService.initiate_subscription_purchase(
                self.test_user.user_id, 'javascript', 'yearly'
            )
            
            self.assertTrue(success)
            self.assertEqual(result['purchase_data']['subscription_type'], 'yearly')
            self.assertEqual(result['purchase_data']['amount'], 299.99)
    
    def test_initiate_purchase_with_existing_subscription(self):
        """Test initiating purchase when subscription already exists"""
        with self.app.app_context():
            success, result = PaymentGateService.initiate_subscription_purchase(
                self.test_user_with_sub.user_id, 'python', 'monthly'
            )
            
            self.assertFalse(success)
            self.assertEqual(result['error'], 'SUBSCRIPTION_EXISTS')
            self.assertIn('subscription', result)
    
    def test_complete_subscription_purchase(self):
        """Test completing subscription purchase"""
        with self.app.app_context():
            # Complete monthly purchase
            success, result = PaymentGateService.complete_subscription_purchase(
                self.test_user.user_id, 'python', 'monthly', 'payment_ref_123'
            )
            
            self.assertTrue(success)
            self.assertIn('subscription', result)
            self.assertEqual(result['subscription']['status'], 'active')
            self.assertEqual(result['subscription']['subject'], 'python')
            self.assertEqual(result['payment_reference'], 'payment_ref_123')
            
            # Verify subscription was created
            from app.services.subscription_service import SubscriptionService
            subscription = SubscriptionService.get_subscription(self.test_user.user_id, 'python')
            self.assertIsNotNone(subscription)
            self.assertEqual(subscription.status, 'active')
    
    def test_validate_payment_amount(self):
        """Test payment amount validation"""
        with self.app.app_context():
            # Test valid amounts
            is_valid, expected = PaymentGateService.validate_payment_amount('python', 'monthly', 29.99)
            self.assertTrue(is_valid)
            self.assertEqual(expected, 29.99)
            
            is_valid, expected = PaymentGateService.validate_payment_amount('python', 'yearly', 299.99)
            self.assertTrue(is_valid)
            self.assertEqual(expected, 299.99)
            
            # Test invalid amounts
            is_valid, expected = PaymentGateService.validate_payment_amount('python', 'monthly', 25.00)
            self.assertFalse(is_valid)
            self.assertEqual(expected, 29.99)
            
            # Test invalid subject
            is_valid, expected = PaymentGateService.validate_payment_amount('invalid', 'monthly', 29.99)
            self.assertFalse(is_valid)
            self.assertEqual(expected, 0.0)
    
    def test_get_subscription_pricing(self):
        """Test getting subscription pricing"""
        with self.app.app_context():
            pricing = PaymentGateService.get_subscription_pricing('python')
            self.assertIsNotNone(pricing)
            self.assertEqual(pricing['monthly'], 29.99)
            self.assertEqual(pricing['yearly'], 299.99)
            
            # Test invalid subject
            pricing = PaymentGateService.get_subscription_pricing('invalid')
            self.assertIsNone(pricing)


class TestSubscriptionExpirationHandling(unittest.TestCase):
    """Test subscription expiration handling"""
    
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
    
    def test_handle_subscription_expiration(self):
        """Test handling expired subscriptions"""
        with self.app.app_context():
            from app.services.subscription_service import SubscriptionService
            
            # Create expired subscription
            expired_sub = SubscriptionService.create_subscription(
                self.test_user.user_id, 'python', 'active',
                expires_at=datetime.utcnow() - timedelta(days=1)
            )
            
            # Create active subscription
            active_sub = SubscriptionService.create_subscription(
                self.test_user.user_id, 'javascript', 'active',
                expires_at=datetime.utcnow() + timedelta(days=30)
            )
            
            # Handle expiration
            processed_count, expired_list = PaymentGateService.handle_subscription_expiration()
            
            self.assertEqual(processed_count, 1)
            self.assertEqual(len(expired_list), 1)
            self.assertEqual(expired_list[0]['subject'], 'python')
            
            # Verify subscription status was updated
            updated_sub = SubscriptionService.get_subscription(self.test_user.user_id, 'python')
            self.assertEqual(updated_sub.status, 'expired')
            
            # Verify active subscription wasn't affected
            active_sub_check = SubscriptionService.get_subscription(self.test_user.user_id, 'javascript')
            self.assertEqual(active_sub_check.status, 'active')
    
    def test_expired_subscription_access_denied(self):
        """Test that expired subscriptions deny access"""
        with self.app.app_context():
            from app.services.subscription_service import SubscriptionService
            
            # Create expired subscription
            SubscriptionService.create_subscription(
                self.test_user.user_id, 'python', 'active',
                expires_at=datetime.utcnow() - timedelta(days=1)
            )
            
            # Check access should be denied
            has_access, reason, details = PaymentGateService.check_subject_access(self.test_user.user_id, 'python')
            self.assertFalse(has_access)
            self.assertEqual(reason, 'SUBSCRIPTION_REQUIRED')
    
    def test_get_user_payment_summary(self):
        """Test getting user payment summary"""
        with self.app.app_context():
            from app.services.subscription_service import SubscriptionService
            
            # Create multiple subscriptions
            SubscriptionService.create_subscription(
                self.test_user.user_id, 'python', 'active',
                expires_at=datetime.utcnow() + timedelta(days=30)
            )
            SubscriptionService.create_subscription(
                self.test_user.user_id, 'javascript', 'expired',
                expires_at=datetime.utcnow() - timedelta(days=1)
            )
            
            summary = PaymentGateService.get_user_payment_summary(self.test_user.user_id)
            
            self.assertIsNotNone(summary)
            self.assertEqual(summary['user_id'], self.test_user.user_id)
            self.assertEqual(summary['total_subscriptions'], 2)
            self.assertEqual(summary['active_subscriptions'], 1)
            self.assertGreater(summary['estimated_total_spent'], 0)
            self.assertEqual(len(summary['subscriptions']), 2)
            self.assertEqual(len(summary['active_only']), 1)


class TestPaymentGateIntegration(unittest.TestCase):
    """Test payment gate integration with API endpoints"""
    
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
    
    def test_end_to_end_purchase_workflow(self):
        """Test complete purchase workflow from initiation to completion"""
        # Step 1: Check initial access (should be denied)
        response = self.client.get(f'/api/users/{self.test_user.user_id}/subjects/python/access')
        self.assertEqual(response.status_code, 402)
        
        # Step 2: Purchase subscription
        response = self.client.post(
            f'/api/users/{self.test_user.user_id}/subscriptions/python',
            json={'type': 'monthly'}
        )
        self.assertEqual(response.status_code, 201)
        
        # Step 3: Check access again (should be granted)
        response = self.client.get(f'/api/users/{self.test_user.user_id}/subjects/python/access')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertTrue(data['access_granted'])
        
        # Step 4: Select subject (should work now)
        response = self.client.post(f'/api/users/{self.test_user.user_id}/subjects/python/select')
        self.assertEqual(response.status_code, 200)
    
    def test_subscription_expiration_workflow(self):
        """Test subscription expiration workflow"""
        with self.app.app_context():
            from app.services.subscription_service import SubscriptionService
            
            # Create subscription that will expire soon
            SubscriptionService.create_subscription(
                self.test_user.user_id, 'python', 'active',
                expires_at=datetime.utcnow() + timedelta(seconds=1)
            )
        
        # Initially should have access
        response = self.client.get(f'/api/users/{self.test_user.user_id}/subjects/python/access')
        self.assertEqual(response.status_code, 200)
        
        # Wait for expiration (in real scenario, this would be handled by background job)
        time.sleep(2)
        
        # Check access after expiration
        response = self.client.get(f'/api/users/{self.test_user.user_id}/subjects/python/access')
        self.assertEqual(response.status_code, 402)  # Should be denied due to expiration
    
    def test_multiple_subject_subscriptions(self):
        """Test managing multiple subject subscriptions"""
        # Purchase multiple subscriptions
        subjects = ['python', 'javascript', 'react']
        
        for subject in subjects:
            response = self.client.post(
                f'/api/users/{self.test_user.user_id}/subscriptions/{subject}',
                json={'type': 'monthly'}
            )
            self.assertEqual(response.status_code, 201)
        
        # Check that all subjects are accessible
        for subject in subjects:
            response = self.client.get(f'/api/users/{self.test_user.user_id}/subjects/{subject}/access')
            self.assertEqual(response.status_code, 200)
            data = json.loads(response.data)
            self.assertTrue(data['access_granted'])
        
        # List active subscriptions
        response = self.client.get(f'/api/users/{self.test_user.user_id}/subscriptions/active')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertEqual(data['count'], 3)
        
        # Cancel one subscription
        response = self.client.delete(f'/api/users/{self.test_user.user_id}/subscriptions/python')
        self.assertEqual(response.status_code, 200)
        
        # Check that cancelled subject is no longer accessible
        response = self.client.get(f'/api/users/{self.test_user.user_id}/subjects/python/access')
        self.assertEqual(response.status_code, 402)
        
        # Other subjects should still be accessible
        for subject in ['javascript', 'react']:
            response = self.client.get(f'/api/users/{self.test_user.user_id}/subjects/{subject}/access')
            self.assertEqual(response.status_code, 200)
    
    def test_payment_gate_error_handling(self):
        """Test payment gate error handling"""
        # Test with invalid user
        response = self.client.get('/api/users/invalid_user/subjects/python/access')
        self.assertEqual(response.status_code, 404)
        
        # Test with invalid subject
        response = self.client.get('/api/users/test_user/subjects/invalid_subject/access')
        self.assertEqual(response.status_code, 404)
        
        # Test purchasing invalid subject
        response = self.client.post(
            '/api/users/test_user/subscriptions/invalid_subject',
            json={'type': 'monthly'}
        )
        self.assertEqual(response.status_code, 400)


if __name__ == '__main__':
    unittest.main()