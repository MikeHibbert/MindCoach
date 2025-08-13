"""
Authentication API endpoints for user registration, login, and token management
"""
from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity, get_jwt
from app.services.auth_service import AuthService
from app.utils.validation import validate_json
from app.utils.security import log_api_request
from marshmallow import Schema, fields, validate
from sqlalchemy.exc import SQLAlchemyError

auth_bp = Blueprint('auth', __name__)

# Validation schemas
class RegisterSchema(Schema):
    user_id = fields.Str(required=True, validate=validate.Length(min=3, max=50))
    email = fields.Email(required=True, validate=validate.Length(max=100))
    password = fields.Str(required=True, validate=validate.Length(min=8))

class LoginSchema(Schema):
    email = fields.Email(required=True)
    password = fields.Str(required=True)

class ChangePasswordSchema(Schema):
    old_password = fields.Str(required=True)
    new_password = fields.Str(required=True, validate=validate.Length(min=8))


@auth_bp.route('/auth/register', methods=['POST'])
@log_api_request
@validate_json(RegisterSchema)
def register():
    """Register a new user"""
    try:
        data = request.validated_data
        user_id = data['user_id']
        email = data['email']
        password = data['password']
        
        # Register user
        user, access_token, refresh_token = AuthService.register_user(user_id, email, password)
        
        return jsonify({
            'message': 'User registered successfully',
            'user': user.to_dict(),
            'access_token': access_token,
            'refresh_token': refresh_token
        }), 201
        
    except ValueError as e:
        return jsonify({
            'error': {
                'code': 'VALIDATION_ERROR',
                'message': str(e),
                'details': None
            }
        }), 400
    except SQLAlchemyError as e:
        current_app.logger.error(f'Database error during registration: {str(e)}')
        return jsonify({
            'error': {
                'code': 'DATABASE_ERROR',
                'message': 'Failed to register user',
                'details': None
            }
        }), 500
    except Exception as e:
        current_app.logger.error(f'Unexpected error during registration: {str(e)}')
        return jsonify({
            'error': {
                'code': 'INTERNAL_SERVER_ERROR',
                'message': 'An unexpected error occurred',
                'details': None
            }
        }), 500


@auth_bp.route('/auth/login', methods=['POST'])
@log_api_request
@validate_json(LoginSchema)
def login():
    """Login user and return tokens"""
    try:
        data = request.validated_data
        email = data['email']
        password = data['password']
        
        # Authenticate user
        user, access_token, refresh_token = AuthService.login_user(email, password)
        
        return jsonify({
            'message': 'Login successful',
            'user': user.to_dict(),
            'access_token': access_token,
            'refresh_token': refresh_token
        }), 200
        
    except ValueError as e:
        return jsonify({
            'error': {
                'code': 'AUTHENTICATION_ERROR',
                'message': str(e),
                'details': None
            }
        }), 401
    except SQLAlchemyError as e:
        current_app.logger.error(f'Database error during login: {str(e)}')
        return jsonify({
            'error': {
                'code': 'DATABASE_ERROR',
                'message': 'Failed to authenticate user',
                'details': None
            }
        }), 500
    except Exception as e:
        current_app.logger.error(f'Unexpected error during login: {str(e)}')
        return jsonify({
            'error': {
                'code': 'INTERNAL_SERVER_ERROR',
                'message': 'An unexpected error occurred',
                'details': None
            }
        }), 500


@auth_bp.route('/auth/refresh', methods=['POST'])
@jwt_required(refresh=True)
@log_api_request
def refresh():
    """Refresh access token"""
    try:
        access_token = AuthService.refresh_token()
        
        return jsonify({
            'access_token': access_token
        }), 200
        
    except ValueError as e:
        return jsonify({
            'error': {
                'code': 'AUTHENTICATION_ERROR',
                'message': str(e),
                'details': None
            }
        }), 401
    except Exception as e:
        current_app.logger.error(f'Unexpected error during token refresh: {str(e)}')
        return jsonify({
            'error': {
                'code': 'INTERNAL_SERVER_ERROR',
                'message': 'An unexpected error occurred',
                'details': None
            }
        }), 500


@auth_bp.route('/auth/logout', methods=['POST'])
@jwt_required()
@log_api_request
def logout():
    """Logout user by blacklisting token"""
    try:
        AuthService.logout_user()
        
        return jsonify({
            'message': 'Logout successful'
        }), 200
        
    except Exception as e:
        current_app.logger.error(f'Unexpected error during logout: {str(e)}')
        return jsonify({
            'error': {
                'code': 'INTERNAL_SERVER_ERROR',
                'message': 'An unexpected error occurred',
                'details': None
            }
        }), 500


@auth_bp.route('/auth/me', methods=['GET'])
@jwt_required()
@log_api_request
def get_current_user():
    """Get current authenticated user"""
    try:
        user = AuthService.get_current_user()
        
        if not user:
            return jsonify({
                'error': {
                    'code': 'USER_NOT_FOUND',
                    'message': 'User not found',
                    'details': None
                }
            }), 404
        
        return jsonify({
            'user': user.to_dict()
        }), 200
        
    except Exception as e:
        current_app.logger.error(f'Unexpected error getting current user: {str(e)}')
        return jsonify({
            'error': {
                'code': 'INTERNAL_SERVER_ERROR',
                'message': 'An unexpected error occurred',
                'details': None
            }
        }), 500


@auth_bp.route('/auth/change-password', methods=['POST'])
@jwt_required()
@log_api_request
@validate_json(ChangePasswordSchema)
def change_password():
    """Change user password"""
    try:
        data = request.validated_data
        current_user_id = get_jwt_identity()
        old_password = data['old_password']
        new_password = data['new_password']
        
        # Change password
        AuthService.change_password(current_user_id, old_password, new_password)
        
        return jsonify({
            'message': 'Password changed successfully'
        }), 200
        
    except ValueError as e:
        return jsonify({
            'error': {
                'code': 'VALIDATION_ERROR',
                'message': str(e),
                'details': None
            }
        }), 400
    except SQLAlchemyError as e:
        current_app.logger.error(f'Database error during password change: {str(e)}')
        return jsonify({
            'error': {
                'code': 'DATABASE_ERROR',
                'message': 'Failed to change password',
                'details': None
            }
        }), 500
    except Exception as e:
        current_app.logger.error(f'Unexpected error during password change: {str(e)}')
        return jsonify({
            'error': {
                'code': 'INTERNAL_SERVER_ERROR',
                'message': 'An unexpected error occurred',
                'details': None
            }
        }), 500


@auth_bp.route('/auth/validate', methods=['GET'])
@jwt_required()
@log_api_request
def validate_token():
    """Validate current token"""
    try:
        current_user_id = get_jwt_identity()
        user = AuthService.get_current_user()
        
        if not user or not user.is_active:
            return jsonify({
                'error': {
                    'code': 'INVALID_TOKEN',
                    'message': 'Token is invalid or user is inactive',
                    'details': None
                }
            }), 401
        
        return jsonify({
            'valid': True,
            'user_id': current_user_id
        }), 200
        
    except Exception as e:
        current_app.logger.error(f'Unexpected error during token validation: {str(e)}')
        return jsonify({
            'error': {
                'code': 'INTERNAL_SERVER_ERROR',
                'message': 'An unexpected error occurred',
                'details': None
            }
        }), 500