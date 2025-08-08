"""Input validation utilities for API endpoints"""
import re
from functools import wraps
from flask import request, jsonify
from marshmallow import Schema, fields, ValidationError


def validate_json(schema_class):
    """Decorator to validate JSON input against a Marshmallow schema"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not request.is_json:
                return jsonify({
                    'error': {
                        'code': 'INVALID_CONTENT_TYPE',
                        'message': 'Content-Type must be application/json',
                        'details': None
                    }
                }), 400
            
            try:
                schema = schema_class()
                validated_data = schema.load(request.json)
                request.validated_data = validated_data
                return f(*args, **kwargs)
            except ValidationError as err:
                return jsonify({
                    'error': {
                        'code': 'VALIDATION_ERROR',
                        'message': 'Invalid input data',
                        'details': err.messages
                    }
                }), 400
            except Exception as err:
                return jsonify({
                    'error': {
                        'code': 'INVALID_JSON',
                        'message': 'Invalid JSON format',
                        'details': str(err)
                    }
                }), 400
        
        return decorated_function
    return decorator


def validate_user_id(user_id):
    """Validate user ID format"""
    if not user_id or not isinstance(user_id, str):
        return False
    
    # User ID should be alphanumeric with optional hyphens/underscores
    pattern = r'^[a-zA-Z0-9_-]+$'
    return bool(re.match(pattern, user_id)) and len(user_id) <= 50


def validate_subject(subject):
    """Validate subject name format"""
    if not subject or not isinstance(subject, str):
        return False
    
    # Subject should be lowercase alphanumeric with optional hyphens
    pattern = r'^[a-z0-9-]+$'
    return bool(re.match(pattern, subject)) and len(subject) <= 50


def validate_lesson_id(lesson_id):
    """Validate lesson ID format"""
    if not lesson_id or not isinstance(lesson_id, str):
        return False
    
    # Lesson ID should be numeric or in format lesson_N
    pattern = r'^(lesson_)?\d+$'
    return bool(re.match(pattern, lesson_id))


# Marshmallow schemas for request validation
class UserCreateSchema(Schema):
    user_id = fields.Str(required=True, validate=lambda x: validate_user_id(x))
    email = fields.Email(required=False, allow_none=True)


class UserUpdateSchema(Schema):
    email = fields.Email(required=False, allow_none=True)


class SubjectSelectionSchema(Schema):
    pass  # No additional data required for subject selection


class SurveySubmissionSchema(Schema):
    answers = fields.List(fields.Dict(), required=True)