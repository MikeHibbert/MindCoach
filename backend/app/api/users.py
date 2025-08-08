from flask import Blueprint, request, jsonify, current_app
from app.services.user_service import UserService
from app.services.user_data_service import UserDataService
from app.utils.validation import validate_json, validate_user_id, UserCreateSchema, UserUpdateSchema
from app.utils.security import log_api_request
from sqlalchemy.exc import SQLAlchemyError
import os

users_bp = Blueprint('users', __name__)


@users_bp.route('/users', methods=['POST'])
@log_api_request
@validate_json(UserCreateSchema)
def create_user():
    """Create a new user"""
    try:
        data = request.validated_data
        user_id = data['user_id']
        email = data.get('email')
        
        # Validate user_id format
        if not validate_user_id(user_id):
            return jsonify({
                'error': {
                    'code': 'INVALID_USER_ID',
                    'message': 'Invalid user ID format',
                    'details': 'User ID must be alphanumeric with optional hyphens/underscores, max 50 characters'
                }
            }), 400
        
        # Create user in database
        user = UserService.create_user(user_id, email)
        
        # Create user directory structure
        from app.services.file_service import FileService
        FileService.ensure_user_directory(user_id)
        
        current_app.logger.info(f'User created successfully: {user_id}')
        
        return jsonify({
            'message': 'User created successfully',
            'user': user.to_dict()
        }), 201
        
    except SQLAlchemyError as e:
        current_app.logger.error(f'Database error creating user: {str(e)}')
        return jsonify({
            'error': {
                'code': 'DATABASE_ERROR',
                'message': 'Failed to create user',
                'details': None
            }
        }), 500
    except OSError as e:
        current_app.logger.error(f'File system error creating user directory: {str(e)}')
        return jsonify({
            'error': {
                'code': 'FILESYSTEM_ERROR',
                'message': 'Failed to create user directory',
                'details': None
            }
        }), 500
    except Exception as e:
        current_app.logger.error(f'Unexpected error creating user: {str(e)}')
        return jsonify({
            'error': {
                'code': 'INTERNAL_SERVER_ERROR',
                'message': 'An unexpected error occurred',
                'details': None
            }
        }), 500


@users_bp.route('/users/<user_id>', methods=['GET'])
@log_api_request
def get_user(user_id):
    """Get user profile by user_id"""
    try:
        # Validate user_id format
        if not validate_user_id(user_id):
            return jsonify({
                'error': {
                    'code': 'INVALID_USER_ID',
                    'message': 'Invalid user ID format',
                    'details': 'User ID must be alphanumeric with optional hyphens/underscores, max 50 characters'
                }
            }), 400
        
        # Get user from database
        user = UserService.get_user_by_id(user_id)
        
        if not user:
            return jsonify({
                'error': {
                    'code': 'USER_NOT_FOUND',
                    'message': 'User not found',
                    'details': f'No user found with ID: {user_id}'
                }
            }), 404
        
        return jsonify({
            'user': user.to_dict()
        }), 200
        
    except SQLAlchemyError as e:
        current_app.logger.error(f'Database error getting user {user_id}: {str(e)}')
        return jsonify({
            'error': {
                'code': 'DATABASE_ERROR',
                'message': 'Failed to retrieve user',
                'details': None
            }
        }), 500
    except Exception as e:
        current_app.logger.error(f'Unexpected error getting user {user_id}: {str(e)}')
        return jsonify({
            'error': {
                'code': 'INTERNAL_SERVER_ERROR',
                'message': 'An unexpected error occurred',
                'details': None
            }
        }), 500


@users_bp.route('/users/<user_id>', methods=['PUT'])
@log_api_request
@validate_json(UserUpdateSchema)
def update_user(user_id):
    """Update user profile"""
    try:
        # Validate user_id format
        if not validate_user_id(user_id):
            return jsonify({
                'error': {
                    'code': 'INVALID_USER_ID',
                    'message': 'Invalid user ID format',
                    'details': 'User ID must be alphanumeric with optional hyphens/underscores, max 50 characters'
                }
            }), 400
        
        data = request.validated_data
        
        # Check if user exists
        existing_user = UserService.get_user_by_id(user_id)
        if not existing_user:
            return jsonify({
                'error': {
                    'code': 'USER_NOT_FOUND',
                    'message': 'User not found',
                    'details': f'No user found with ID: {user_id}'
                }
            }), 404
        
        # Update user
        updated_user = UserService.update_user(user_id, **data)
        
        if not updated_user:
            return jsonify({
                'error': {
                    'code': 'UPDATE_FAILED',
                    'message': 'Failed to update user',
                    'details': None
                }
            }), 500
        
        current_app.logger.info(f'User updated successfully: {user_id}')
        
        return jsonify({
            'message': 'User updated successfully',
            'user': updated_user.to_dict()
        }), 200
        
    except SQLAlchemyError as e:
        current_app.logger.error(f'Database error updating user {user_id}: {str(e)}')
        return jsonify({
            'error': {
                'code': 'DATABASE_ERROR',
                'message': 'Failed to update user',
                'details': None
            }
        }), 500
    except Exception as e:
        current_app.logger.error(f'Unexpected error updating user {user_id}: {str(e)}')
        return jsonify({
            'error': {
                'code': 'INTERNAL_SERVER_ERROR',
                'message': 'An unexpected error occurred',
                'details': None
            }
        }), 500