"""
Authentication decorators and utilities for protecting API endpoints
"""
from functools import wraps
from flask import jsonify, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity, verify_jwt_in_request, get_jwt
from app.services.auth_service import AuthService

def auth_required(f):
    """
    Decorator that requires valid JWT authentication
    """
    @wraps(f)
    @jwt_required()
    def decorated_function(*args, **kwargs):
        try:
            # Check if token is blacklisted
            jti = get_jwt()['jti']
            if AuthService.is_token_blacklisted(jti):
                return jsonify({
                    'error': {
                        'code': 'TOKEN_BLACKLISTED',
                        'message': 'Token has been revoked',
                        'details': None
                    }
                }), 401
            
            # Check if user exists and is active
            user = AuthService.get_current_user()
            if not user or not user.is_active:
                return jsonify({
                    'error': {
                        'code': 'USER_INACTIVE',
                        'message': 'User account is inactive',
                        'details': None
                    }
                }), 401
            
            return f(*args, **kwargs)
            
        except Exception as e:
            current_app.logger.error(f'Authentication error: {str(e)}')
            return jsonify({
                'error': {
                    'code': 'AUTHENTICATION_ERROR',
                    'message': 'Authentication failed',
                    'details': None
                }
            }), 401
    
    return decorated_function

def optional_auth(f):
    """
    Decorator that allows optional JWT authentication
    Sets current_user in kwargs if authenticated
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        try:
            # Try to verify JWT
            verify_jwt_in_request(optional=True)
            
            current_user_id = get_jwt_identity()
            if current_user_id:
                # Check if token is blacklisted
                jti = get_jwt()['jti']
                if not AuthService.is_token_blacklisted(jti):
                    user = AuthService.get_current_user()
                    if user and user.is_active:
                        kwargs['current_user'] = user
            
            return f(*args, **kwargs)
            
        except Exception as e:
            # If authentication fails, continue without user
            current_app.logger.debug(f'Optional authentication failed: {str(e)}')
            return f(*args, **kwargs)
    
    return decorated_function

def admin_required(f):
    """
    Decorator that requires admin privileges
    Note: This is a placeholder - implement admin role system as needed
    """
    @wraps(f)
    @auth_required
    def decorated_function(*args, **kwargs):
        try:
            user = AuthService.get_current_user()
            
            # For now, check if user_id contains 'admin'
            # In production, implement proper role-based access control
            if not user or 'admin' not in user.user_id.lower():
                return jsonify({
                    'error': {
                        'code': 'INSUFFICIENT_PRIVILEGES',
                        'message': 'Admin privileges required',
                        'details': None
                    }
                }), 403
            
            return f(*args, **kwargs)
            
        except Exception as e:
            current_app.logger.error(f'Admin authorization error: {str(e)}')
            return jsonify({
                'error': {
                    'code': 'AUTHORIZATION_ERROR',
                    'message': 'Authorization failed',
                    'details': None
                }
            }), 403
    
    return decorated_function

def user_owns_resource(resource_user_id_param='user_id'):
    """
    Decorator that ensures the authenticated user owns the resource
    
    Args:
        resource_user_id_param (str): Name of the parameter containing the resource user_id
    """
    def decorator(f):
        @wraps(f)
        @auth_required
        def decorated_function(*args, **kwargs):
            try:
                current_user_id = get_jwt_identity()
                resource_user_id = kwargs.get(resource_user_id_param)
                
                if not resource_user_id:
                    return jsonify({
                        'error': {
                            'code': 'MISSING_RESOURCE_ID',
                            'message': 'Resource user ID not provided',
                            'details': None
                        }
                    }), 400
                
                if current_user_id != resource_user_id:
                    return jsonify({
                        'error': {
                            'code': 'ACCESS_DENIED',
                            'message': 'You can only access your own resources',
                            'details': None
                        }
                    }), 403
                
                return f(*args, **kwargs)
                
            except Exception as e:
                current_app.logger.error(f'Resource ownership check error: {str(e)}')
                return jsonify({
                    'error': {
                        'code': 'AUTHORIZATION_ERROR',
                        'message': 'Authorization failed',
                        'details': None
                    }
                }), 403
        
        return decorated_function
    return decorator