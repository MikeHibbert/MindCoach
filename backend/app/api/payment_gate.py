"""
Payment gate API endpoints for subscription purchase workflows
"""

from flask import Blueprint, request, jsonify
from app.services.payment_gate_service import PaymentGateService
from app.services.user_service import UserService
from app.utils.validation import validate_user_id, validate_subject
import logging

logger = logging.getLogger(__name__)

payment_gate_bp = Blueprint('payment_gate', __name__)

@payment_gate_bp.route('/users/<user_id>/subjects/<subject>/access-check', methods=['GET'])
def check_access(user_id, subject):
    """Check if user has access to subject (payment gate)"""
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
        
        # Check access using payment gate service
        has_access, reason, details = PaymentGateService.check_subject_access(user_id, subject)
        
        if not has_access:
            return jsonify({
                'access_granted': False,
                'reason': reason,
                'details': details
            }), 402 if reason == 'SUBSCRIPTION_REQUIRED' else 400
        
        return jsonify({
            'access_granted': True,
            'reason': reason,
            'details': details
        }), 200
        
    except Exception as e:
        logger.error(f"Error checking access for user {user_id}, subject {subject}: {str(e)}")
        return jsonify({
            'error': {
                'code': 'INTERNAL_ERROR',
                'message': 'Failed to check access'
            }
        }), 500

@payment_gate_bp.route('/users/<user_id>/subjects/<subject>/purchase/initiate', methods=['POST'])
def initiate_purchase(user_id, subject):
    """Initiate subscription purchase workflow"""
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
        
        # Get request data
        data = request.get_json() or {}
        subscription_type = data.get('subscription_type', 'monthly')
        
        # Initiate purchase
        success, result = PaymentGateService.initiate_subscription_purchase(
            user_id, subject, subscription_type
        )
        
        if not success:
            error_code = result.get('error', 'PURCHASE_FAILED')
            status_code = 409 if error_code == 'SUBSCRIPTION_EXISTS' else 400
            return jsonify(result), status_code
        
        logger.info(f"Purchase initiated: {user_id} - {subject} ({subscription_type})")
        
        return jsonify(result), 200
        
    except Exception as e:
        logger.error(f"Error initiating purchase for user {user_id}, subject {subject}: {str(e)}")
        return jsonify({
            'error': 'INTERNAL_ERROR',
            'message': 'Failed to initiate purchase'
        }), 500

@payment_gate_bp.route('/users/<user_id>/subjects/<subject>/purchase/complete', methods=['POST'])
def complete_purchase(user_id, subject):
    """Complete subscription purchase after payment processing"""
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
        
        # Get request data
        data = request.get_json() or {}
        subscription_type = data.get('subscription_type', 'monthly')
        payment_reference = data.get('payment_reference')
        payment_amount = data.get('payment_amount')
        
        # Validate payment amount if provided
        if payment_amount:
            is_valid, expected_amount = PaymentGateService.validate_payment_amount(
                subject, subscription_type, payment_amount
            )
            if not is_valid:
                return jsonify({
                    'error': 'INVALID_PAYMENT_AMOUNT',
                    'message': f'Payment amount {payment_amount} does not match expected {expected_amount}',
                    'expected_amount': expected_amount
                }), 400
        
        # Complete purchase
        success, result = PaymentGateService.complete_subscription_purchase(
            user_id, subject, subscription_type, payment_reference
        )
        
        if not success:
            error_code = result.get('error', 'PURCHASE_COMPLETION_FAILED')
            status_code = 404 if error_code == 'USER_NOT_FOUND' else 400
            return jsonify(result), status_code
        
        logger.info(f"Purchase completed: {user_id} - {subject} ({subscription_type})")
        
        return jsonify(result), 201
        
    except Exception as e:
        logger.error(f"Error completing purchase for user {user_id}, subject {subject}: {str(e)}")
        return jsonify({
            'error': 'INTERNAL_ERROR',
            'message': 'Failed to complete purchase'
        }), 500

@payment_gate_bp.route('/users/<user_id>/payment-summary', methods=['GET'])
def get_payment_summary(user_id):
    """Get payment summary for a user"""
    try:
        # Validate inputs
        if not validate_user_id(user_id):
            return jsonify({
                'error': {
                    'code': 'INVALID_USER_ID',
                    'message': 'Invalid user ID format'
                }
            }), 400
        
        # Get payment summary
        summary = PaymentGateService.get_user_payment_summary(user_id)
        
        if summary is None:
            return jsonify({
                'error': {
                    'code': 'USER_NOT_FOUND',
                    'message': 'User not found'
                }
            }), 404
        
        return jsonify(summary), 200
        
    except Exception as e:
        logger.error(f"Error getting payment summary for user {user_id}: {str(e)}")
        return jsonify({
            'error': {
                'code': 'INTERNAL_ERROR',
                'message': 'Failed to get payment summary'
            }
        }), 500

@payment_gate_bp.route('/subjects/<subject>/pricing', methods=['GET'])
def get_subject_pricing(subject):
    """Get pricing information for a subject"""
    try:
        # Validate subject
        if not validate_subject(subject):
            return jsonify({
                'error': {
                    'code': 'INVALID_SUBJECT',
                    'message': 'Invalid subject format'
                }
            }), 400
        
        # Get pricing
        pricing = PaymentGateService.get_subscription_pricing(subject)
        
        if pricing is None:
            return jsonify({
                'error': {
                    'code': 'SUBJECT_NOT_FOUND',
                    'message': 'Subject not found'
                }
            }), 404
        
        return jsonify({
            'subject': subject,
            'pricing': pricing
        }), 200
        
    except Exception as e:
        logger.error(f"Error getting pricing for subject {subject}: {str(e)}")
        return jsonify({
            'error': {
                'code': 'INTERNAL_ERROR',
                'message': 'Failed to get pricing'
            }
        }), 500

@payment_gate_bp.route('/admin/subscriptions/expired/process', methods=['POST'])
def process_expired_subscriptions():
    """Process expired subscriptions (admin endpoint)"""
    try:
        # Handle subscription expiration
        processed_count, expired_list = PaymentGateService.handle_subscription_expiration()
        
        return jsonify({
            'processed_count': processed_count,
            'expired_subscriptions': expired_list,
            'message': f'Processed {processed_count} expired subscriptions'
        }), 200
        
    except Exception as e:
        logger.error(f"Error processing expired subscriptions: {str(e)}")
        return jsonify({
            'error': {
                'code': 'INTERNAL_ERROR',
                'message': 'Failed to process expired subscriptions'
            }
        }), 500