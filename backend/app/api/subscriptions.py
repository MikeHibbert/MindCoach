from flask import Blueprint, request, jsonify
from app.services.subscription_service import SubscriptionService
from app.services.user_service import UserService
from app.utils.validation import validate_user_id, validate_subject
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

subscriptions_bp = Blueprint('subscriptions', __name__)

# Available subjects configuration (should match subjects.py)
AVAILABLE_SUBJECTS = {
    'python': {
        'name': 'Python Programming',
        'description': 'Learn Python from basics to advanced concepts',
        'price_monthly': 29.99,
        'price_yearly': 299.99
    },
    'javascript': {
        'name': 'JavaScript Development',
        'description': 'Master JavaScript for web development',
        'price_monthly': 29.99,
        'price_yearly': 299.99
    },
    'react': {
        'name': 'React Framework',
        'description': 'Build modern web applications with React',
        'price_monthly': 34.99,
        'price_yearly': 349.99
    },
    'nodejs': {
        'name': 'Node.js Backend',
        'description': 'Server-side development with Node.js',
        'price_monthly': 34.99,
        'price_yearly': 349.99
    },
    'sql': {
        'name': 'SQL Database',
        'description': 'Database design and SQL queries',
        'price_monthly': 24.99,
        'price_yearly': 249.99
    },
    'therapy': {
        'name': 'Therapy and Counseling',
        'description': 'Learn therapeutic techniques and counseling skills',
        'price_monthly': 0.00,  # Free subject for demo
        'price_yearly': 0.00
    }
}

@subscriptions_bp.route('/users/<user_id>/subscriptions', methods=['GET'])
def get_user_subscriptions(user_id):
    """Get all subscriptions for a user"""
    try:
        # Validate inputs
        if not validate_user_id(user_id):
            return jsonify({
                'error': {
                    'code': 'INVALID_USER_ID',
                    'message': 'Invalid user ID format'
                }
            }), 400
        
        # Check if user exists
        user = UserService.get_user_by_id(user_id)
        if not user:
            return jsonify({
                'error': {
                    'code': 'USER_NOT_FOUND',
                    'message': 'User not found'
                }
            }), 404
        
        # Get all subscriptions for user
        subscriptions = SubscriptionService.get_user_subscriptions(user_id)
        active_subscriptions = SubscriptionService.get_active_subscriptions(user_id)
        
        # Format subscription data
        subscription_data = []
        for sub in subscriptions:
            sub_dict = sub.to_dict()
            # Add subject information
            if sub.subject in AVAILABLE_SUBJECTS:
                sub_dict['subject_info'] = {
                    'name': AVAILABLE_SUBJECTS[sub.subject]['name'],
                    'description': AVAILABLE_SUBJECTS[sub.subject]['description']
                }
            subscription_data.append(sub_dict)
        
        active_subscription_data = []
        for sub in active_subscriptions:
            sub_dict = sub.to_dict()
            # Add subject information
            if sub.subject in AVAILABLE_SUBJECTS:
                sub_dict['subject_info'] = {
                    'name': AVAILABLE_SUBJECTS[sub.subject]['name'],
                    'description': AVAILABLE_SUBJECTS[sub.subject]['description']
                }
            active_subscription_data.append(sub_dict)
        
        return jsonify({
            'user_id': user_id,
            'subscriptions': subscription_data,
            'active_subscriptions': active_subscription_data,
            'total_subscriptions': len(subscription_data),
            'active_count': len(active_subscription_data)
        }), 200
        
    except Exception as e:
        logger.error(f"Error getting subscriptions for user {user_id}: {str(e)}")
        return jsonify({
            'error': {
                'code': 'INTERNAL_ERROR',
                'message': 'Failed to retrieve subscriptions'
            }
        }), 500

@subscriptions_bp.route('/users/<user_id>/subscriptions/<subject>', methods=['POST'])
def purchase_subscription(user_id, subject):
    """Purchase a subscription for a subject"""
    try:
        # Validate inputs
        if not validate_user_id(user_id):
            return jsonify({
                'error': {
                    'code': 'INVALID_USER_ID',
                    'message': 'Invalid user ID format'
                }
            }), 400
        
        if not validate_subject(subject):
            return jsonify({
                'error': {
                    'code': 'INVALID_SUBJECT',
                    'message': 'Invalid subject format'
                }
            }), 400
        
        # Check if subject exists
        if subject not in AVAILABLE_SUBJECTS:
            return jsonify({
                'error': {
                    'code': 'SUBJECT_NOT_FOUND',
                    'message': 'Subject not found'
                }
            }), 404
        
        # Check if user exists
        user = UserService.get_user_by_id(user_id)
        if not user:
            return jsonify({
                'error': {
                    'code': 'USER_NOT_FOUND',
                    'message': 'User not found'
                }
            }), 404
        
        # Get request data
        data = request.get_json() or {}
        plan = data.get('plan', 'monthly')  # Default to monthly
        payment_method = data.get('payment_method', 'mock')
        
        # Validate plan
        if plan not in ['monthly', 'yearly']:
            return jsonify({
                'error': {
                    'code': 'INVALID_PLAN',
                    'message': 'Plan must be either monthly or yearly'
                }
            }), 400
        
        # Check if user already has active subscription
        existing_subscription = SubscriptionService.get_subscription(user_id, subject)
        if existing_subscription and existing_subscription.status == 'active':
            # Check if it's still valid
            if not existing_subscription.expires_at or existing_subscription.expires_at > datetime.utcnow():
                return jsonify({
                    'error': {
                        'code': 'SUBSCRIPTION_EXISTS',
                        'message': 'User already has an active subscription for this subject',
                        'subscription': existing_subscription.to_dict()
                    }
                }), 409  # Conflict
        
        # Calculate expiration date
        expires_at = None
        if plan == 'monthly':
            expires_at = datetime.utcnow() + timedelta(days=30)
        elif plan == 'yearly':
            expires_at = datetime.utcnow() + timedelta(days=365)
        
        # Mock payment processing (in real implementation, integrate with payment provider)
        if payment_method == 'mock':
            # Simulate payment processing
            payment_success = True  # In real implementation, call payment API
            transaction_id = f"mock_txn_{user_id}_{subject}_{datetime.utcnow().timestamp()}"
        else:
            return jsonify({
                'error': {
                    'code': 'PAYMENT_METHOD_NOT_SUPPORTED',
                    'message': 'Only mock payment method is currently supported'
                }
            }), 400
        
        if not payment_success:
            return jsonify({
                'error': {
                    'code': 'PAYMENT_FAILED',
                    'message': 'Payment processing failed'
                }
            }), 402  # Payment Required
        
        # Create or update subscription
        if existing_subscription:
            subscription = SubscriptionService.update_subscription(
                user_id, subject,
                status='active',
                expires_at=expires_at,
                updated_at=datetime.utcnow()
            )
        else:
            subscription = SubscriptionService.create_subscription(
                user_id=user_id,
                subject=subject,
                status='active',
                expires_at=expires_at
            )
        
        if not subscription:
            return jsonify({
                'error': {
                    'code': 'SUBSCRIPTION_CREATION_FAILED',
                    'message': 'Failed to create subscription'
                }
            }), 500
        
        logger.info(f"Subscription purchased: {user_id} - {subject} - {plan}")
        
        # Return success response
        response_data = {
            'message': f'Successfully purchased {plan} subscription for {AVAILABLE_SUBJECTS[subject]["name"]}',
            'subscription': subscription.to_dict(),
            'subject_info': {
                'id': subject,
                'name': AVAILABLE_SUBJECTS[subject]['name'],
                'description': AVAILABLE_SUBJECTS[subject]['description']
            },
            'payment': {
                'transaction_id': transaction_id,
                'plan': plan,
                'amount': AVAILABLE_SUBJECTS[subject][f'price_{plan}'],
                'processed_at': datetime.utcnow().isoformat()
            }
        }
        
        return jsonify(response_data), 201
        
    except Exception as e:
        logger.error(f"Error purchasing subscription for user {user_id}, subject {subject}: {str(e)}")
        return jsonify({
            'error': {
                'code': 'INTERNAL_ERROR',
                'message': 'Failed to purchase subscription'
            }
        }), 500

@subscriptions_bp.route('/users/<user_id>/subscriptions/<subject>', methods=['DELETE'])
def cancel_subscription(user_id, subject):
    """Cancel a subscription for a subject"""
    try:
        # Validate inputs
        if not validate_user_id(user_id):
            return jsonify({
                'error': {
                    'code': 'INVALID_USER_ID',
                    'message': 'Invalid user ID format'
                }
            }), 400
        
        if not validate_subject(subject):
            return jsonify({
                'error': {
                    'code': 'INVALID_SUBJECT',
                    'message': 'Invalid subject format'
                }
            }), 400
        
        # Check if subject exists
        if subject not in AVAILABLE_SUBJECTS:
            return jsonify({
                'error': {
                    'code': 'SUBJECT_NOT_FOUND',
                    'message': 'Subject not found'
                }
            }), 404
        
        # Check if user exists
        user = UserService.get_user_by_id(user_id)
        if not user:
            return jsonify({
                'error': {
                    'code': 'USER_NOT_FOUND',
                    'message': 'User not found'
                }
            }), 404
        
        # Get existing subscription
        subscription = SubscriptionService.get_subscription(user_id, subject)
        if not subscription:
            return jsonify({
                'error': {
                    'code': 'SUBSCRIPTION_NOT_FOUND',
                    'message': 'No subscription found for this subject'
                }
            }), 404
        
        if subscription.status != 'active':
            return jsonify({
                'error': {
                    'code': 'SUBSCRIPTION_NOT_ACTIVE',
                    'message': 'Subscription is not active and cannot be cancelled'
                }
            }), 400
        
        # Cancel subscription
        cancelled_subscription = SubscriptionService.cancel_subscription(user_id, subject)
        if not cancelled_subscription:
            return jsonify({
                'error': {
                    'code': 'CANCELLATION_FAILED',
                    'message': 'Failed to cancel subscription'
                }
            }), 500
        
        logger.info(f"Subscription cancelled: {user_id} - {subject}")
        
        return jsonify({
            'message': f'Successfully cancelled subscription for {AVAILABLE_SUBJECTS[subject]["name"]}',
            'subscription': cancelled_subscription.to_dict(),
            'subject_info': {
                'id': subject,
                'name': AVAILABLE_SUBJECTS[subject]['name']
            },
            'cancelled_at': datetime.utcnow().isoformat()
        }), 200
        
    except Exception as e:
        logger.error(f"Error cancelling subscription for user {user_id}, subject {subject}: {str(e)}")
        return jsonify({
            'error': {
                'code': 'INTERNAL_ERROR',
                'message': 'Failed to cancel subscription'
            }
        }), 500

@subscriptions_bp.route('/users/<user_id>/subscriptions/<subject>/status', methods=['GET'])
def get_subscription_status(user_id, subject):
    """Get detailed subscription status for a specific subject"""
    try:
        # Validate inputs
        if not validate_user_id(user_id):
            return jsonify({
                'error': {
                    'code': 'INVALID_USER_ID',
                    'message': 'Invalid user ID format'
                }
            }), 400
        
        if not validate_subject(subject):
            return jsonify({
                'error': {
                    'code': 'INVALID_SUBJECT',
                    'message': 'Invalid subject format'
                }
            }), 400
        
        # Check if subject exists
        if subject not in AVAILABLE_SUBJECTS:
            return jsonify({
                'error': {
                    'code': 'SUBJECT_NOT_FOUND',
                    'message': 'Subject not found'
                }
            }), 404
        
        # Check if user exists
        user = UserService.get_user_by_id(user_id)
        if not user:
            return jsonify({
                'error': {
                    'code': 'USER_NOT_FOUND',
                    'message': 'User not found'
                }
            }), 404
        
        # Get subscription and status
        subscription = SubscriptionService.get_subscription(user_id, subject)
        has_active = SubscriptionService.has_active_subscription(user_id, subject)
        
        response_data = {
            'user_id': user_id,
            'subject': {
                'id': subject,
                'name': AVAILABLE_SUBJECTS[subject]['name'],
                'description': AVAILABLE_SUBJECTS[subject]['description']
            },
            'subscription': subscription.to_dict() if subscription else None,
            'status': {
                'has_active_subscription': has_active,
                'can_access_content': has_active,
                'requires_payment': not has_active
            },
            'pricing': {
                'monthly': AVAILABLE_SUBJECTS[subject]['price_monthly'],
                'yearly': AVAILABLE_SUBJECTS[subject]['price_yearly']
            }
        }
        
        return jsonify(response_data), 200
        
    except Exception as e:
        logger.error(f"Error getting subscription status for user {user_id}, subject {subject}: {str(e)}")
        return jsonify({
            'error': {
                'code': 'INTERNAL_ERROR',
                'message': 'Failed to get subscription status'
            }
        }), 500