from flask import Blueprint, request, jsonify
from app.services.subscription_service import SubscriptionService
from app.services.user_service import UserService
from app.utils.validation import validate_user_id, validate_subject
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

subscriptions_bp = Blueprint('subscriptions', __name__)

@subscriptions_bp.route('/users/<user_id>/subscriptions', methods=['GET'])
def list_subscriptions(user_id):
    """List all subscriptions for a user"""
    try:
        # Validate user_id
        if not validate_user_id(user_id):
            return jsonify({
                'error': {
                    'code': 'INVALID_USER_ID',
                    'message': 'Invalid user ID format'
                }
            }), 400
        
        # Check if user exists
        user = UserService.get_user(user_id)
        if not user:
            return jsonify({
                'error': {
                    'code': 'USER_NOT_FOUND',
                    'message': 'User not found'
                }
            }), 404
        
        # Get all subscriptions for user
        subscriptions = SubscriptionService.get_user_subscriptions(user_id)
        
        return jsonify({
            'subscriptions': [sub.to_dict() for sub in subscriptions]
        }), 200
        
    except Exception as e:
        logger.error(f"Error listing subscriptions for user {user_id}: {str(e)}")
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
        
        # Check if user exists
        user = UserService.get_user(user_id)
        if not user:
            return jsonify({
                'error': {
                    'code': 'USER_NOT_FOUND',
                    'message': 'User not found'
                }
            }), 404
        
        # Get request data
        data = request.get_json() or {}
        subscription_type = data.get('type', 'monthly')  # monthly or yearly
        
        # Calculate expiration date
        if subscription_type == 'yearly':
            expires_at = datetime.utcnow() + timedelta(days=365)
        else:  # monthly
            expires_at = datetime.utcnow() + timedelta(days=30)
        
        # Check if subscription already exists
        existing_subscription = SubscriptionService.get_subscription(user_id, subject)
        if existing_subscription and existing_subscription.status == 'active':
            # Check if it's still valid
            if not existing_subscription.expires_at or existing_subscription.expires_at > datetime.utcnow():
                return jsonify({
                    'error': {
                        'code': 'SUBSCRIPTION_EXISTS',
                        'message': 'Active subscription already exists for this subject',
                        'details': {
                            'subscription': existing_subscription.to_dict()
                        }
                    }
                }), 409
        
        # Create or update subscription
        if existing_subscription:
            subscription = SubscriptionService.update_subscription(
                user_id, subject, 
                status='active',
                expires_at=expires_at,
                purchased_at=datetime.utcnow()
            )
        else:
            subscription = SubscriptionService.create_subscription(
                user_id, subject, 
                status='active',
                expires_at=expires_at
            )
        
        logger.info(f"Subscription purchased: {user_id} - {subject} ({subscription_type})")
        
        return jsonify({
            'subscription': subscription.to_dict(),
            'message': f'Successfully purchased {subscription_type} subscription for {subject}'
        }), 201
        
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
        
        # Check if user exists
        user = UserService.get_user(user_id)
        if not user:
            return jsonify({
                'error': {
                    'code': 'USER_NOT_FOUND',
                    'message': 'User not found'
                }
            }), 404
        
        # Check if subscription exists
        subscription = SubscriptionService.get_subscription(user_id, subject)
        if not subscription:
            return jsonify({
                'error': {
                    'code': 'SUBSCRIPTION_NOT_FOUND',
                    'message': 'Subscription not found'
                }
            }), 404
        
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
            'subscription': cancelled_subscription.to_dict(),
            'message': f'Successfully cancelled subscription for {subject}'
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
def check_subscription_status(user_id, subject):
    """Check subscription status for a specific subject"""
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
        
        # Check if user exists
        user = UserService.get_user(user_id)
        if not user:
            return jsonify({
                'error': {
                    'code': 'USER_NOT_FOUND',
                    'message': 'User not found'
                }
            }), 404
        
        # Check subscription status
        has_active = SubscriptionService.has_active_subscription(user_id, subject)
        subscription = SubscriptionService.get_subscription(user_id, subject)
        
        response_data = {
            'user_id': user_id,
            'subject': subject,
            'has_active_subscription': has_active,
            'subscription': subscription.to_dict() if subscription else None
        }
        
        return jsonify(response_data), 200
        
    except Exception as e:
        logger.error(f"Error checking subscription status for user {user_id}, subject {subject}: {str(e)}")
        return jsonify({
            'error': {
                'code': 'INTERNAL_ERROR',
                'message': 'Failed to check subscription status'
            }
        }), 500

@subscriptions_bp.route('/users/<user_id>/subscriptions/active', methods=['GET'])
def list_active_subscriptions(user_id):
    """List all active subscriptions for a user"""
    try:
        # Validate user_id
        if not validate_user_id(user_id):
            return jsonify({
                'error': {
                    'code': 'INVALID_USER_ID',
                    'message': 'Invalid user ID format'
                }
            }), 400
        
        # Check if user exists
        user = UserService.get_user(user_id)
        if not user:
            return jsonify({
                'error': {
                    'code': 'USER_NOT_FOUND',
                    'message': 'User not found'
                }
            }), 404
        
        # Get active subscriptions
        active_subscriptions = SubscriptionService.get_active_subscriptions(user_id)
        
        return jsonify({
            'active_subscriptions': [sub.to_dict() for sub in active_subscriptions],
            'count': len(active_subscriptions)
        }), 200
        
    except Exception as e:
        logger.error(f"Error listing active subscriptions for user {user_id}: {str(e)}")
        return jsonify({
            'error': {
                'code': 'INTERNAL_ERROR',
                'message': 'Failed to retrieve active subscriptions'
            }
        }), 500