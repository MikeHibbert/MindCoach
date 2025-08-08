"""Security utilities and middleware"""
import os
import re
from functools import wraps
from flask import request, jsonify, current_app


def sanitize_path(path):
    """Sanitize file paths to prevent directory traversal attacks"""
    if not path:
        return None
    
    # Remove any path traversal attempts
    path = re.sub(r'\.\./', '', path)
    path = re.sub(r'\.\.\\', '', path)
    
    # Remove any absolute path indicators
    path = path.lstrip('/')
    path = path.lstrip('\\')
    
    return path


def validate_file_path(base_dir, file_path):
    """Validate that a file path is within the allowed base directory"""
    try:
        # Normalize paths
        base_dir = os.path.abspath(base_dir)
        full_path = os.path.abspath(os.path.join(base_dir, file_path))
        
        # Check if the full path is within the base directory
        return full_path.startswith(base_dir)
    except (ValueError, OSError):
        return False


def rate_limit_check(max_requests=100, window_minutes=60):
    """Basic rate limiting decorator (in production, use Redis or similar)"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # In a production environment, implement proper rate limiting
            # using Redis or a similar solution
            return f(*args, **kwargs)
        return decorated_function
    return decorator


def require_subscription(f):
    """Decorator to check if user has active subscription for subject"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        user_id = kwargs.get('user_id')
        subject = kwargs.get('subject')
        
        if not user_id or not subject:
            return jsonify({
                'error': {
                    'code': 'MISSING_PARAMETERS',
                    'message': 'User ID and subject are required',
                    'details': None
                }
            }), 400
        
        # Import here to avoid circular imports
        from app.services.subscription_service import SubscriptionService
        
        subscription_service = SubscriptionService()
        if not subscription_service.has_active_subscription(user_id, subject):
            return jsonify({
                'error': {
                    'code': 'SUBSCRIPTION_REQUIRED',
                    'message': 'Active subscription required for this subject',
                    'details': {
                        'subject': subject,
                        'available_plans': ['monthly', 'yearly']
                    }
                }
            }), 403
        
        return f(*args, **kwargs)
    return decorated_function


def log_api_request(f):
    """Decorator to log API requests"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        current_app.logger.info(
            f'API Request: {request.method} {request.path} '
            f'from {request.remote_addr}'
        )
        return f(*args, **kwargs)
    return decorated_function