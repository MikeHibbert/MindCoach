from flask import Blueprint, request, jsonify
import logging

from app.services.lesson_generation_service import LessonGenerationService
from app.services.lesson_file_service import LessonFileService
from app.services.subscription_service import SubscriptionService
from app.utils.validation import validate_user_id, validate_subject

logger = logging.getLogger(__name__)

lessons_bp = Blueprint('lessons', __name__)

@lessons_bp.route('/users/<user_id>/subjects/<subject>/lessons/generate', methods=['POST'])
def generate_lessons(user_id, subject):
    """Generate personalized lessons for a user and subject"""
    try:
        # Validate input parameters
        if not validate_user_id(user_id):
            return jsonify({
                'success': False,
                'error': 'validation_error',
                'message': 'Invalid user ID format'
            }), 400
        
        if not validate_subject(subject):
            return jsonify({
                'success': False,
                'error': 'validation_error',
                'message': 'Invalid subject format'
            }), 400
        
        logger.info(f"Generating lessons for user {user_id}, subject {subject}")
        
        # Check if user has active subscription for the subject
        try:
            has_subscription = SubscriptionService.has_active_subscription(user_id, subject)
            if not has_subscription:
                logger.warning(f"User {user_id} attempted to generate lessons for {subject} without subscription")
                return jsonify({
                    'success': False,
                    'error': 'subscription_required',
                    'message': f'Active subscription required for {subject}',
                    'details': {
                        'subject': subject,
                        'user_id': user_id
                    }
                }), 403
        except Exception as e:
            logger.error(f"Error checking subscription for {user_id} - {subject}: {str(e)}")
            # Continue with lesson generation if subscription check fails (graceful degradation)
        
        # Generate personalized lessons
        generation_result = LessonGenerationService.generate_personalized_lessons(user_id, subject)
        
        lessons = generation_result['lessons']
        metadata = generation_result['metadata']
        
        # Save lessons to file system
        save_result = LessonFileService.save_lessons(user_id, subject, lessons, metadata)
        
        logger.info(f"Lessons generated and saved for {user_id} - {subject}: {save_result['saved_successfully']} lessons")
        
        # Return generation summary
        response_data = {
            'success': True,
            'generation_summary': {
                'user_id': user_id,
                'subject': subject,
                'skill_level': metadata['skill_level'],
                'total_lessons': metadata['total_lessons'],
                'generated_at': metadata['generated_at'],
                'topic_analysis': metadata['topic_analysis']
            },
            'save_summary': {
                'saved_successfully': save_result['saved_successfully'],
                'failed_saves': save_result['failed_saves'],
                'saved_files': save_result['saved_files']
            },
            'message': f'Successfully generated {save_result["saved_successfully"]} personalized lessons for {subject}'
        }
        
        if save_result['failed_files']:
            response_data['warnings'] = [f"Some lessons failed to save: {len(save_result['failed_files'])} out of {len(lessons)}"]
        
        return jsonify(response_data), 201
        
    except ValueError as e:
        logger.warning(f"Validation error generating lessons: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'validation_error',
            'message': str(e)
        }), 400
        
    except FileNotFoundError as e:
        logger.warning(f"Survey results not found for lesson generation: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'prerequisite_missing',
            'message': 'Survey results not found. Please complete the subject survey first.',
            'details': {
                'required_action': 'complete_survey',
                'subject': subject
            }
        }), 404
        
    except Exception as e:
        logger.error(f"Error generating lessons for {user_id} - {subject}: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'generation_error',
            'message': 'Failed to generate lessons'
        }), 500

@lessons_bp.route('/users/<user_id>/subjects/<subject>/lessons', methods=['GET'])
def list_lessons(user_id, subject):
    """List available lessons for a user and subject"""
    try:
        # Validate input parameters
        if not validate_user_id(user_id):
            return jsonify({
                'success': False,
                'error': 'validation_error',
                'message': 'Invalid user ID format'
            }), 400
        
        if not validate_subject(subject):
            return jsonify({
                'success': False,
                'error': 'validation_error',
                'message': 'Invalid subject format'
            }), 400
        
        logger.info(f"Listing lessons for user {user_id}, subject {subject}")
        
        # Check if user has active subscription for the subject
        try:
            has_subscription = SubscriptionService.has_active_subscription(user_id, subject)
            if not has_subscription:
                logger.warning(f"User {user_id} attempted to access lessons for {subject} without subscription")
                return jsonify({
                    'success': False,
                    'error': 'subscription_required',
                    'message': f'Active subscription required for {subject}',
                    'details': {
                        'subject': subject,
                        'user_id': user_id
                    }
                }), 403
        except Exception as e:
            logger.error(f"Error checking subscription for {user_id} - {subject}: {str(e)}")
            # Continue with lesson listing if subscription check fails (graceful degradation)
        
        # Get lesson list
        lesson_list = LessonFileService.list_lessons(user_id, subject)
        
        logger.info(f"Listed {lesson_list['total_lessons']} lessons for {user_id} - {subject}")
        
        return jsonify({
            'success': True,
            'lessons': lesson_list['lessons'],
            'summary': {
                'user_id': lesson_list['user_id'],
                'subject': lesson_list['subject'],
                'total_lessons': lesson_list['total_lessons'],
                'skill_level': lesson_list.get('skill_level'),
                'generated_at': lesson_list.get('generated_at')
            }
        }), 200
        
    except ValueError as e:
        logger.warning(f"Validation error listing lessons: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'validation_error',
            'message': str(e)
        }), 400
        
    except Exception as e:
        logger.error(f"Error listing lessons for {user_id} - {subject}: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'retrieval_error',
            'message': 'Failed to retrieve lesson list'
        }), 500

@lessons_bp.route('/users/<user_id>/subjects/<subject>/lessons/<int:lesson_number>', methods=['GET'])
def get_lesson(user_id, subject, lesson_number):
    """Retrieve a specific lesson by number"""
    try:
        # Validate input parameters
        if not validate_user_id(user_id):
            return jsonify({
                'success': False,
                'error': 'validation_error',
                'message': 'Invalid user ID format'
            }), 400
        
        if not validate_subject(subject):
            return jsonify({
                'success': False,
                'error': 'validation_error',
                'message': 'Invalid subject format'
            }), 400
        
        logger.info(f"Retrieving lesson {lesson_number} for user {user_id}, subject {subject}")
        
        # Check if user has active subscription for the subject
        try:
            has_subscription = SubscriptionService.has_active_subscription(user_id, subject)
            if not has_subscription:
                logger.warning(f"User {user_id} attempted to access lesson {lesson_number} for {subject} without subscription")
                return jsonify({
                    'success': False,
                    'error': 'subscription_required',
                    'message': f'Active subscription required for {subject}',
                    'details': {
                        'subject': subject,
                        'user_id': user_id,
                        'lesson_number': lesson_number
                    }
                }), 403
        except Exception as e:
            logger.error(f"Error checking subscription for {user_id} - {subject}: {str(e)}")
            # Continue with lesson retrieval if subscription check fails (graceful degradation)
        
        # Get the specific lesson
        lesson = LessonFileService.get_lesson(user_id, subject, lesson_number)
        
        logger.info(f"Retrieved lesson {lesson_number} for {user_id} - {subject}: {lesson['title']}")
        
        return jsonify({
            'success': True,
            'lesson': {
                'lesson_number': lesson['lesson_number'],
                'title': lesson['title'],
                'estimated_time': lesson['estimated_time'],
                'difficulty': lesson['difficulty'],
                'topics': lesson['topics'],
                'content': lesson['content'],
                'loaded_at': lesson['loaded_at']
            }
        }), 200
        
    except ValueError as e:
        logger.warning(f"Validation error retrieving lesson: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'validation_error',
            'message': str(e)
        }), 400
        
    except FileNotFoundError as e:
        logger.info(f"Lesson not found: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'not_found',
            'message': f'Lesson {lesson_number} not found for {subject}',
            'details': {
                'lesson_number': lesson_number,
                'subject': subject,
                'user_id': user_id
            }
        }), 404
        
    except Exception as e:
        logger.error(f"Error retrieving lesson {lesson_number} for {user_id} - {subject}: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'retrieval_error',
            'message': 'Failed to retrieve lesson'
        }), 500

@lessons_bp.route('/users/<user_id>/subjects/<subject>/lessons', methods=['DELETE'])
def delete_lessons(user_id, subject):
    """Delete all lessons for a user and subject"""
    try:
        # Validate input parameters
        if not validate_user_id(user_id):
            return jsonify({
                'success': False,
                'error': 'validation_error',
                'message': 'Invalid user ID format'
            }), 400
        
        if not validate_subject(subject):
            return jsonify({
                'success': False,
                'error': 'validation_error',
                'message': 'Invalid subject format'
            }), 400
        
        logger.info(f"Deleting lessons for user {user_id}, subject {subject}")
        
        # Delete lessons
        delete_result = LessonFileService.delete_lessons(user_id, subject)
        
        logger.info(f"Deleted {delete_result['total_deleted']} files for {user_id} - {subject}")
        
        return jsonify({
            'success': True,
            'deletion_summary': {
                'user_id': delete_result['user_id'],
                'subject': delete_result['subject'],
                'total_deleted': delete_result['total_deleted'],
                'deleted_files': delete_result['deleted_files'],
                'deleted_at': delete_result['deleted_at']
            },
            'message': f'Successfully deleted {delete_result["total_deleted"]} lesson files for {subject}'
        }), 200
        
    except ValueError as e:
        logger.warning(f"Validation error deleting lessons: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'validation_error',
            'message': str(e)
        }), 400
        
    except Exception as e:
        logger.error(f"Error deleting lessons for {user_id} - {subject}: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'deletion_error',
            'message': 'Failed to delete lessons'
        }), 500

@lessons_bp.route('/users/<user_id>/subjects/<subject>/lessons/progress', methods=['GET'])
def get_lesson_progress(user_id, subject):
    """Get lesson progress summary for a user and subject"""
    try:
        # Validate input parameters
        if not validate_user_id(user_id):
            return jsonify({
                'success': False,
                'error': 'validation_error',
                'message': 'Invalid user ID format'
            }), 400
        
        if not validate_subject(subject):
            return jsonify({
                'success': False,
                'error': 'validation_error',
                'message': 'Invalid subject format'
            }), 400
        
        logger.info(f"Getting lesson progress for user {user_id}, subject {subject}")
        
        # Get lesson list to determine progress
        lesson_list = LessonFileService.list_lessons(user_id, subject)
        
        # Calculate progress metrics
        total_lessons = lesson_list['total_lessons']
        available_lessons = sum(1 for lesson in lesson_list['lessons'] if lesson.get('file_exists', False))
        
        progress_percentage = (available_lessons / 10) * 100 if total_lessons > 0 else 0  # Assuming max 10 lessons
        
        progress_summary = {
            'user_id': user_id,
            'subject': subject,
            'total_lessons_generated': total_lessons,
            'available_lessons': available_lessons,
            'progress_percentage': round(progress_percentage, 1),
            'skill_level': lesson_list.get('skill_level'),
            'generated_at': lesson_list.get('generated_at'),
            'lessons': [
                {
                    'lesson_number': lesson['lesson_number'],
                    'title': lesson['title'],
                    'available': lesson.get('file_exists', False),
                    'estimated_time': lesson['estimated_time'],
                    'difficulty': lesson['difficulty']
                }
                for lesson in lesson_list['lessons']
            ]
        }
        
        logger.info(f"Progress retrieved for {user_id} - {subject}: {available_lessons}/{total_lessons} lessons available")
        
        return jsonify({
            'success': True,
            'progress': progress_summary
        }), 200
        
    except ValueError as e:
        logger.warning(f"Validation error getting lesson progress: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'validation_error',
            'message': str(e)
        }), 400
        
    except Exception as e:
        logger.error(f"Error getting lesson progress for {user_id} - {subject}: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'retrieval_error',
            'message': 'Failed to retrieve lesson progress'
        }), 500