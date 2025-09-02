from flask import Blueprint, request, jsonify
from app.services.user_service import UserService
from app.services.user_data_service import UserDataService
from app.utils.validation import validate_user_id, validate_subject
import logging

logger = logging.getLogger(__name__)

subjects_bp = Blueprint('subjects', __name__)

# Available subjects configuration
AVAILABLE_SUBJECTS = {
    'python': {
        'name': 'Python Programming',
        'description': 'Learn Python from basics to advanced concepts'
    },
    'javascript': {
        'name': 'JavaScript Development',
        'description': 'Master JavaScript for web development'
    },
    'react': {
        'name': 'React Framework',
        'description': 'Build modern web applications with React'
    },
    'nodejs': {
        'name': 'Node.js Backend',
        'description': 'Server-side development with Node.js'
    },
    'sql': {
        'name': 'SQL Database',
        'description': 'Database design and SQL queries'
    },
    'therapy': {
        'name': 'Therapy',
        'description': 'Mental health and therapeutic techniques'
    }
}

@subjects_bp.route('/subjects', methods=['GET', 'POST'])
def handle_subjects():
    """Handle both listing subjects (GET) and adding new subjects (POST)"""
    if request.method == 'GET':
        return list_subjects()
    elif request.method == 'POST':
        return add_subject()

def list_subjects():
    """List all available subjects"""
    try:
        user_id = request.args.get('user_id')
        
        subjects_list = []
        
        # Add predefined subjects
        for subject_key, subject_info in AVAILABLE_SUBJECTS.items():
            subject_data = {
                'id': subject_key,
                'name': subject_info['name'],
                'description': subject_info['description'],
                'available': True,
                'type': 'predefined'
            }
            
            subjects_list.append(subject_data)
        
        # Add user-generated subjects if user_id provided (including anonymous)
        if user_id:
            try:
                user_subjects = UserDataService.get_user_subjects(user_id)
                for subject_key in user_subjects:
                    # Skip if already in predefined subjects
                    if subject_key in AVAILABLE_SUBJECTS:
                        continue
                    
                    # Create subject data for user-generated subject
                    subject_data = {
                        'id': subject_key,
                        'name': subject_key.replace('-', ' ').title(),
                        'description': f'Personalized learning content for {subject_key.replace("-", " ").title()}',
                        'available': True,
                        'type': 'user_generated'
                    }
                    
                    subjects_list.append(subject_data)
                    
            except Exception as e:
                logger.warning(f"Could not get user subjects for {user_id}: {str(e)}")
        
        return jsonify({
            'subjects': subjects_list,
            'total_count': len(subjects_list)
        }), 200
        
    except Exception as e:
        logger.error(f"Error listing subjects: {str(e)}")
        return jsonify({
            'error': {
                'code': 'INTERNAL_ERROR',
                'message': 'Failed to retrieve subjects'
            }
        }), 500

def add_subject():
    """Add a new subject to the available subjects list"""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({
                'error': {
                    'code': 'INVALID_REQUEST',
                    'message': 'Request body is required'
                }
            }), 400
        
        # Validate required fields
        name = data.get('name', '').strip()
        description = data.get('description', '').strip()
        
        if not name:
            return jsonify({
                'error': {
                    'code': 'MISSING_NAME',
                    'message': 'Subject name is required'
                }
            }), 400
        
        if not description:
            return jsonify({
                'error': {
                    'code': 'MISSING_DESCRIPTION',
                    'message': 'Subject description is required'
                }
            }), 400
        
        # Generate subject ID from name (lowercase, replace spaces with hyphens)
        subject_id = name.lower().replace(' ', '-').replace('_', '-')
        
        # Remove any non-alphanumeric characters except hyphens
        import re
        subject_id = re.sub(r'[^a-z0-9-]', '', subject_id)
        
        # Check if subject already exists
        if subject_id in AVAILABLE_SUBJECTS:
            return jsonify({
                'error': {
                    'code': 'SUBJECT_EXISTS',
                    'message': f'Subject with name "{name}" already exists'
                }
            }), 409
        
        # Add new subject to the available subjects
        AVAILABLE_SUBJECTS[subject_id] = {
            'name': name,
            'description': description
        }
        
        # Create response subject data
        subject_data = {
            'id': subject_id,
            'name': name,
            'description': description,
            'available': True,
            'type': 'predefined'
        }
        
        logger.info(f"New subject added: {subject_id} - {name}")
        
        return jsonify({
            'message': f'Subject "{name}" added successfully',
            'subject': subject_data
        }), 201
        
    except Exception as e:
        logger.error(f"Error adding subject: {str(e)}")
        return jsonify({
            'error': {
                'code': 'INTERNAL_ERROR',
                'message': 'Failed to add subject'
            }
        }), 500

@subjects_bp.route('/users/<user_id>/subjects/<subject>/select', methods=['POST'])
def select_subject(user_id, subject):
    """Select a subject for learning"""
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
        
        # Save subject selection (no subscription check required)
        selection_saved = UserDataService.save_subject_selection(user_id, subject)
        if not selection_saved:
            return jsonify({
                'error': {
                    'code': 'SELECTION_FAILED',
                    'message': 'Failed to save subject selection'
                }
            }), 500
        
        logger.info(f"Subject selected: {user_id} - {subject}")
        
        return jsonify({
            'message': f'Successfully selected {AVAILABLE_SUBJECTS[subject]["name"]}',
            'subject': {
                'id': subject,
                'name': AVAILABLE_SUBJECTS[subject]['name'],
                'selected_at': 'now'  # UserDataService should return actual timestamp
            }
        }), 200
        
    except Exception as e:
        logger.error(f"Error selecting subject for user {user_id}, subject {subject}: {str(e)}")
        return jsonify({
            'error': {
                'code': 'INTERNAL_ERROR',
                'message': 'Failed to select subject'
            }
        }), 500

