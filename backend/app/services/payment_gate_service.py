"""
Payment gate service for handling subscription access control and purchase workflows
"""

from app.services.subscription_service import SubscriptionService
from app.services.user_service import UserService
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

class PaymentGateService:
    """Service class for payment gate functionality"""
    
    # Subject pricing configuration
    SUBJECT_PRICING = {
        'python': {'monthly': 29.99, 'yearly': 299.99},
        'javascript': {'monthly': 29.99, 'yearly': 299.99},
        'react': {'monthly': 34.99, 'yearly': 349.99},
        'nodejs': {'monthly': 34.99, 'yearly': 349.99},
        'sql': {'monthly': 24.99, 'yearly': 249.99}
    }
    
    @staticmethod
    def check_subject_access(user_id, subject):
        """
        Check if user has access to a subject (payment gate)
        Returns: (has_access: bool, reason: str, details: dict)
        """
        try:
            # Check if user exists
            user = UserService.get_user(user_id)
            if not user:
                return False, 'USER_NOT_FOUND', {'message': 'User not found'}
            
            # Check if subject is valid
            if subject not in PaymentGateService.SUBJECT_PRICING:
                return False, 'INVALID_SUBJECT', {'message': 'Subject not available'}
            
            # Check subscription status
            has_active = SubscriptionService.has_active_subscription(user_id, subject)
            if not has_active:
                subscription = SubscriptionService.get_subscription(user_id, subject)
                pricing = PaymentGateService.SUBJECT_PRICING[subject]
                
                return False, 'SUBSCRIPTION_REQUIRED', {
                    'message': 'Active subscription required',
                    'subject': subject,
                    'pricing': pricing,
                    'current_subscription': subscription.to_dict() if subscription else None
                }
            
            return True, 'ACCESS_GRANTED', {'message': 'Access granted'}
            
        except Exception as e:
            logger.error(f"Error checking subject access for {user_id}, {subject}: {str(e)}")
            return False, 'INTERNAL_ERROR', {'message': 'Failed to check access'}
    
    @staticmethod
    def initiate_subscription_purchase(user_id, subject, subscription_type='monthly'):
        """
        Initiate subscription purchase workflow
        Returns: (success: bool, result: dict)
        """
        try:
            # Validate inputs
            if not UserService.get_user(user_id):
                return False, {
                    'error': 'USER_NOT_FOUND',
                    'message': 'User not found'
                }
            
            if subject not in PaymentGateService.SUBJECT_PRICING:
                return False, {
                    'error': 'INVALID_SUBJECT',
                    'message': 'Subject not available'
                }
            
            if subscription_type not in ['monthly', 'yearly']:
                return False, {
                    'error': 'INVALID_SUBSCRIPTION_TYPE',
                    'message': 'Subscription type must be monthly or yearly'
                }
            
            # Check if user already has active subscription
            has_active = SubscriptionService.has_active_subscription(user_id, subject)
            if has_active:
                existing_subscription = SubscriptionService.get_subscription(user_id, subject)
                return False, {
                    'error': 'SUBSCRIPTION_EXISTS',
                    'message': 'Active subscription already exists',
                    'subscription': existing_subscription.to_dict()
                }
            
            # Get pricing information
            pricing = PaymentGateService.SUBJECT_PRICING[subject]
            amount = pricing[subscription_type]
            
            # Calculate expiration date
            if subscription_type == 'yearly':
                expires_at = datetime.utcnow() + timedelta(days=365)
            else:  # monthly
                expires_at = datetime.utcnow() + timedelta(days=30)
            
            # Create purchase workflow data
            purchase_data = {
                'user_id': user_id,
                'subject': subject,
                'subscription_type': subscription_type,
                'amount': amount,
                'currency': 'USD',
                'expires_at': expires_at,
                'initiated_at': datetime.utcnow()
            }
            
            logger.info(f"Subscription purchase initiated: {user_id} - {subject} ({subscription_type})")
            
            return True, {
                'purchase_data': purchase_data,
                'message': f'Purchase workflow initiated for {subject} ({subscription_type})',
                'next_step': 'PROCESS_PAYMENT'
            }
            
        except Exception as e:
            logger.error(f"Error initiating subscription purchase for {user_id}, {subject}: {str(e)}")
            return False, {
                'error': 'INTERNAL_ERROR',
                'message': 'Failed to initiate purchase'
            }
    
    @staticmethod
    def complete_subscription_purchase(user_id, subject, subscription_type='monthly', payment_reference=None):
        """
        Complete subscription purchase after payment processing
        Returns: (success: bool, subscription: dict)
        """
        try:
            # Validate inputs
            if not UserService.get_user(user_id):
                return False, {'error': 'USER_NOT_FOUND', 'message': 'User not found'}
            
            if subject not in PaymentGateService.SUBJECT_PRICING:
                return False, {'error': 'INVALID_SUBJECT', 'message': 'Subject not available'}
            
            # Calculate expiration date
            if subscription_type == 'yearly':
                expires_at = datetime.utcnow() + timedelta(days=365)
            else:  # monthly
                expires_at = datetime.utcnow() + timedelta(days=30)
            
            # Create or update subscription
            existing_subscription = SubscriptionService.get_subscription(user_id, subject)
            if existing_subscription:
                # Update existing subscription
                subscription = SubscriptionService.update_subscription(
                    user_id, subject,
                    status='active',
                    expires_at=expires_at,
                    purchased_at=datetime.utcnow()
                )
            else:
                # Create new subscription
                subscription = SubscriptionService.create_subscription(
                    user_id, subject,
                    status='active',
                    expires_at=expires_at
                )
            
            if not subscription:
                return False, {
                    'error': 'SUBSCRIPTION_CREATION_FAILED',
                    'message': 'Failed to create subscription'
                }
            
            logger.info(f"Subscription purchase completed: {user_id} - {subject} ({subscription_type})")
            
            return True, {
                'subscription': subscription.to_dict(),
                'message': f'Successfully purchased {subscription_type} subscription for {subject}',
                'payment_reference': payment_reference
            }
            
        except Exception as e:
            logger.error(f"Error completing subscription purchase for {user_id}, {subject}: {str(e)}")
            return False, {
                'error': 'INTERNAL_ERROR',
                'message': 'Failed to complete purchase'
            }
    
    @staticmethod
    def handle_subscription_expiration():
        """
        Handle expired subscriptions by updating their status
        Returns: (processed_count: int, expired_subscriptions: list)
        """
        try:
            expired_subscriptions = SubscriptionService.get_expired_subscriptions()
            processed_count = 0
            
            for subscription in expired_subscriptions:
                try:
                    # Update subscription status to expired
                    updated_subscription = SubscriptionService.update_subscription(
                        subscription.user_id,
                        subscription.subject,
                        status='expired'
                    )
                    
                    if updated_subscription:
                        processed_count += 1
                        logger.info(f"Subscription expired: {subscription.user_id} - {subscription.subject}")
                    
                except Exception as e:
                    logger.error(f"Error processing expired subscription {subscription.id}: {str(e)}")
                    continue
            
            logger.info(f"Processed {processed_count} expired subscriptions")
            
            return processed_count, [sub.to_dict() for sub in expired_subscriptions]
            
        except Exception as e:
            logger.error(f"Error handling subscription expiration: {str(e)}")
            return 0, []
    
    @staticmethod
    def get_subscription_pricing(subject):
        """
        Get pricing information for a subject
        Returns: dict with pricing info or None if subject not found
        """
        return PaymentGateService.SUBJECT_PRICING.get(subject)
    
    @staticmethod
    def validate_payment_amount(subject, subscription_type, amount):
        """
        Validate payment amount against expected pricing
        Returns: (is_valid: bool, expected_amount: float)
        """
        try:
            pricing = PaymentGateService.SUBJECT_PRICING.get(subject)
            if not pricing:
                return False, 0.0
            
            expected_amount = pricing.get(subscription_type)
            if not expected_amount:
                return False, 0.0
            
            # Allow small floating point differences (within 1 cent)
            is_valid = abs(amount - expected_amount) < 0.01
            
            return is_valid, expected_amount
            
        except Exception as e:
            logger.error(f"Error validating payment amount: {str(e)}")
            return False, 0.0
    
    @staticmethod
    def get_user_payment_summary(user_id):
        """
        Get payment summary for a user including all subscriptions and total spent
        Returns: dict with payment summary
        """
        try:
            user = UserService.get_user(user_id)
            if not user:
                return None
            
            subscriptions = SubscriptionService.get_user_subscriptions(user_id)
            active_subscriptions = SubscriptionService.get_active_subscriptions(user_id)
            
            # Calculate estimated total spent (simplified calculation)
            total_estimated = 0.0
            for subscription in subscriptions:
                if subscription.subject in PaymentGateService.SUBJECT_PRICING:
                    # Estimate based on monthly pricing (simplified)
                    pricing = PaymentGateService.SUBJECT_PRICING[subscription.subject]
                    total_estimated += pricing['monthly']
            
            summary = {
                'user_id': user_id,
                'total_subscriptions': len(subscriptions),
                'active_subscriptions': len(active_subscriptions),
                'estimated_total_spent': total_estimated,
                'subscriptions': [sub.to_dict() for sub in subscriptions],
                'active_only': [sub.to_dict() for sub in active_subscriptions]
            }
            
            return summary
            
        except Exception as e:
            logger.error(f"Error getting payment summary for user {user_id}: {str(e)}")
            return None