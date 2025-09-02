from flask import Blueprint, request, jsonify
from app.services.subscription_service import SubscriptionService
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
    """List all available subjects with pricing information"""
    try:
        user_id = request.args.get('user_id')
        
        subjects_list = []
        for subject_key, subject_info in AVAILABLE_SUBJECTS.items():
            subject_data = {
                'id': subject_key,
                'name': subject_info['name'],
                'description': subject_info['description'],
                'pricing': {
                    'monthly': subject_info['price_monthly'],
                    'yearly': subject_info['price_yearly']
                },
                'available': True,
                'locked': True  # Default to locked
            }
            
            # Check subscription status if user_id provided
            if user_id and validate_user_id(user_id):
                try:
                    has_active = SubscriptionService.has_active_subscription(user_id, subject_key)
                    subject_data['locked'] = not has_active
                    subject_data['available'] = True
                except Exception as e:
                    logger.warning(f"Could not check subscription for {user_id}, {subject_key}: {str(e)}")
            
            subjects_list.append(subject_data)
        
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
        
        # Set default pricing
        price_monthly = data.get('price_monthly', 29.99)
        price_yearly = data.get('price_yearly', price_monthly * 10)  # Default to 10x monthly
        
        # Add new subject to the available subjects
        AVAILABLE_SUBJECTS[subject_id] = {
            'name': name,
            'description': description,
            'price_monthly': price_monthly,
            'price_yearly': price_yearly
        }
        
        # Create response subject data
        subject_data = {
            'id': subject_id,
            'name': name,
            'description': description,
            'pricing': {
                'monthly': price_monthly,
                'yearly': price_yearly
            },
            'available': True,
            'locked': True  # Default to locked (requires subscription)
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
    """Select a subject for learning (requires active subscription)"""
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
        
        # Check subscription status (payment gate)
        has_active = SubscriptionService.has_active_subscription(user_id, subject)
        if not has_active:
            subscription = SubscriptionService.get_subscription(user_id, subject)
            return jsonify({
                'error': {
                    'code': 'SUBSCRIPTION_REQUIRED',
                    'message': 'Active subscription required for this subject',
                    'details': {
                        'subject': subject,
                        'subject_name': AVAILABLE_SUBJECTS[subject]['name'],
                        'pricing': {
                            'monthly': AVAILABLE_SUBJECTS[subject]['price_monthly'],
                            'yearly': AVAILABLE_SUBJECTS[subject]['price_yearly']
                        },
                        'current_subscription': subscription.to_dict() if subscription else None
                    }
                }
            }), 402  # Payment Required
        
        # Save subject selection
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

@subjects_bp.route('/users/<user_id>/subjects/<subject>/status', methods=['GET'])
def get_subject_status(user_id, subject):
    """Get subject access status for a user (payment gate check)"""
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
        
        # Check subscription status
        has_active = SubscriptionService.has_active_subscription(user_id, subject)
        subscription = SubscriptionService.get_subscription(user_id, subject)
        
        # Check if subject is selected
        has_selection = UserDataService.has_subject_selection(user_id, subject)
        
        response_data = {
            'user_id': user_id,
            'subject': {
                'id': subject,
                'name': AVAILABLE_SUBJECTS[subject]['name'],
                'description': AVAILABLE_SUBJECTS[subject]['description']
            },
            'access_status': {
                'has_active_subscription': has_active,
                'is_selected': has_selection,
                'can_access_lessons': has_active and has_selection,
                'requires_payment': not has_active
            },
            'subscription': subscription.to_dict() if subscription else None,
            'pricing': {
                'monthly': AVAILABLE_SUBJECTS[subject]['price_monthly'],
                'yearly': AVAILABLE_SUBJECTS[subject]['price_yearly']
            }
        }
        
        return jsonify(response_data), 200
        
    except Exception as e:
        logger.error(f"Error checking subject status for user {user_id}, subject {subject}: {str(e)}")
        return jsonify({
            'error': {
                'code': 'INTERNAL_ERROR',
                'message': 'Failed to check subject status'
            }
        }), 500

@subjects_bp.route('/users/<user_id>/subjects/<subject>/access', methods=['GET'])
def check_subject_access(user_id, subject):
    """Check if user can access subject content (payment gate enforcement)"""
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
        
        # Payment gate check
        has_active = SubscriptionService.has_active_subscription(user_id, subject)
        if not has_active:
            subscription = SubscriptionService.get_subscription(user_id, subject)
            return jsonify({
                'access_granted': False,
                'reason': 'SUBSCRIPTION_REQUIRED',
                'message': 'Active subscription required to access this subject',
                'subject': AVAILABLE_SUBJECTS[subject]['name'],
                'subscription_options': {
                    'monthly': AVAILABLE_SUBJECTS[subject]['price_monthly'],
                    'yearly': AVAILABLE_SUBJECTS[subject]['price_yearly']
                },
                'current_subscription': subscription.to_dict() if subscription else None
            }), 402  # Payment Required
        
        return jsonify({
            'access_granted': True,
            'subject': {
                'id': subject,
                'name': AVAILABLE_SUBJECTS[subject]['name']
            },
            'subscription_expires': SubscriptionService.get_subscription(user_id, subject).expires_at.isoformat() if SubscriptionService.get_subscription(user_id, subject) and SubscriptionService.get_subscription(user_id, subject).expires_at else None
        }), 200
        
    except Exception as e:
        logger.error(f"Error checking subject access for user {user_id}, subject {subject}: {str(e)}")
        return jsonify({
            'error': {
                'code': 'INTERNAL_ERROR',
                'message': 'Failed to check subject access'
            }
        }), 500