from flask import Blueprint, request, jsonify
import logging

from app.services.lesson_generation_service import LessonGenerationService
from app.services.lesson_file_service import LessonFileService
from app.services.subscription_service import SubscriptionService
from app.services.pipeline_orchestrator import get_pipeline_orchestrator
from app.services.user_data_service import UserDataService
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

# New LangChain Pipeline Endpoints

@lessons_bp.route('/users/<user_id>/subjects/<subject>/lessons/generate-langchain', methods=['POST'])
def generate_lessons_langchain(user_id, subject):
    """Generate personalized lessons using LangChain pipeline"""
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
        
        logger.info(f"Starting LangChain lesson generation for user {user_id}, subject {subject}")
        
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
        
        # Load survey data
        survey_data = UserDataService.load_survey_answers(user_id, subject)
        if not survey_data:
            logger.warning(f"Survey results not found for {user_id} - {subject}")
            return jsonify({
                'success': False,
                'error': 'prerequisite_missing',
                'message': 'Survey results not found. Please complete the subject survey first.',
                'details': {
                    'required_action': 'complete_survey',
                    'subject': subject
                }
            }), 404
        
        # Start the LangChain pipeline
        orchestrator = get_pipeline_orchestrator()
        pipeline_id = orchestrator.start_full_pipeline(
            user_id=user_id,
            subject=subject,
            survey_data=survey_data
        )
        
        logger.info(f"LangChain pipeline started for {user_id} - {subject}: {pipeline_id}")
        
        return jsonify({
            'success': True,
            'pipeline_id': pipeline_id,
            'message': f'LangChain lesson generation started for {subject}',
            'generation_method': 'langchain',
            'status': 'started',
            'details': {
                'user_id': user_id,
                'subject': subject,
                'skill_level': survey_data.get('skill_level', 'unknown'),
                'total_stages': 3
            }
        }), 202
        
    except ValueError as e:
        logger.warning(f"Validation error starting LangChain generation: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'validation_error',
            'message': str(e)
        }), 400
        
    except Exception as e:
        logger.error(f"Error starting LangChain generation for {user_id} - {subject}: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'generation_error',
            'message': 'Failed to start LangChain lesson generation'
        }), 500

@lessons_bp.route('/users/<user_id>/subjects/<subject>/lessons/pipeline-status/<pipeline_id>', methods=['GET'])
def get_pipeline_status(user_id, subject, pipeline_id):
    """Get the status of a LangChain pipeline"""
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
        
        logger.debug(f"Getting pipeline status for {pipeline_id}")
        
        # Get pipeline progress
        orchestrator = get_pipeline_orchestrator()
        progress = orchestrator.get_pipeline_progress(pipeline_id)
        
        if not progress:
            logger.warning(f"Pipeline not found: {pipeline_id}")
            return jsonify({
                'success': False,
                'error': 'not_found',
                'message': 'Pipeline not found',
                'pipeline_id': pipeline_id
            }), 404
        
        # Verify pipeline belongs to the user and subject
        if progress['user_id'] != user_id or progress['subject'] != subject:
            logger.warning(f"Pipeline access denied: {pipeline_id} for {user_id}/{subject}")
            return jsonify({
                'success': False,
                'error': 'access_denied',
                'message': 'Pipeline access denied'
            }), 403
        
        return jsonify({
            'success': True,
            'pipeline_status': progress,
            'pipeline_id': pipeline_id
        }), 200
        
    except ValueError as e:
        logger.warning(f"Validation error getting pipeline status: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'validation_error',
            'message': str(e)
        }), 400
        
    except Exception as e:
        logger.error(f"Error getting pipeline status for {pipeline_id}: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'retrieval_error',
            'message': 'Failed to retrieve pipeline status'
        }), 500

@lessons_bp.route('/users/<user_id>/subjects/<subject>/curriculum', methods=['GET'])
def get_curriculum_scheme(user_id, subject):
    """Get the curriculum scheme generated by LangChain"""
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
        
        logger.info(f"Retrieving curriculum scheme for user {user_id}, subject {subject}")
        
        # Load curriculum scheme
        curriculum_data = UserDataService.load_curriculum_scheme(user_id, subject)
        
        if not curriculum_data:
            logger.info(f"Curriculum scheme not found for {user_id} - {subject}")
            return jsonify({
                'success': False,
                'error': 'not_found',
                'message': 'Curriculum scheme not found. Please generate lessons first.',
                'details': {
                    'user_id': user_id,
                    'subject': subject
                }
            }), 404
        
        logger.info(f"Curriculum scheme retrieved for {user_id} - {subject}")
        
        return jsonify({
            'success': True,
            'curriculum': curriculum_data,
            'message': 'Curriculum scheme retrieved successfully'
        }), 200
        
    except ValueError as e:
        logger.warning(f"Validation error retrieving curriculum: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'validation_error',
            'message': str(e)
        }), 400
        
    except Exception as e:
        logger.error(f"Error retrieving curriculum for {user_id} - {subject}: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'retrieval_error',
            'message': 'Failed to retrieve curriculum scheme'
        }), 500

@lessons_bp.route('/users/<user_id>/subjects/<subject>/lesson-plans', methods=['GET'])
def get_lesson_plans(user_id, subject):
    """Get the lesson plans generated by LangChain"""
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
        
        logger.info(f"Retrieving lesson plans for user {user_id}, subject {subject}")
        
        # Load lesson plans
        lesson_plans_data = UserDataService.load_lesson_plans(user_id, subject)
        
        if not lesson_plans_data:
            logger.info(f"Lesson plans not found for {user_id} - {subject}")
            return jsonify({
                'success': False,
                'error': 'not_found',
                'message': 'Lesson plans not found. Please generate lessons first.',
                'details': {
                    'user_id': user_id,
                    'subject': subject
                }
            }), 404
        
        logger.info(f"Lesson plans retrieved for {user_id} - {subject}")
        
        return jsonify({
            'success': True,
            'lesson_plans': lesson_plans_data,
            'message': 'Lesson plans retrieved successfully'
        }), 200
        
    except ValueError as e:
        logger.warning(f"Validation error retrieving lesson plans: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'validation_error',
            'message': str(e)
        }), 400
        
    except Exception as e:
        logger.error(f"Error retrieving lesson plans for {user_id} - {subject}: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'retrieval_error',
            'message': 'Failed to retrieve lesson plans'
        }), 500

@lessons_bp.route('/users/<user_id>/subjects/<subject>/lessons/<int:lesson_id>/langchain', methods=['GET'])
def get_langchain_lesson(user_id, subject, lesson_id):
    """Retrieve a specific lesson generated by LangChain"""
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
        
        logger.info(f"Retrieving LangChain lesson {lesson_id} for user {user_id}, subject {subject}")
        
        # Check if user has active subscription for the subject
        try:
            has_subscription = SubscriptionService.has_active_subscription(user_id, subject)
            if not has_subscription:
                logger.warning(f"User {user_id} attempted to access lesson {lesson_id} for {subject} without subscription")
                return jsonify({
                    'success': False,
                    'error': 'subscription_required',
                    'message': f'Active subscription required for {subject}',
                    'details': {
                        'subject': subject,
                        'user_id': user_id,
                        'lesson_id': lesson_id
                    }
                }), 403
        except Exception as e:
            logger.error(f"Error checking subscription for {user_id} - {subject}: {str(e)}")
            # Continue with lesson retrieval if subscription check fails (graceful degradation)
        
        # Load lesson content
        lesson_content = UserDataService.load_lesson_content(user_id, subject, lesson_id)
        
        if not lesson_content:
            logger.info(f"LangChain lesson {lesson_id} not found for {user_id} - {subject}")
            return jsonify({
                'success': False,
                'error': 'not_found',
                'message': f'Lesson {lesson_id} not found for {subject}',
                'details': {
                    'lesson_id': lesson_id,
                    'subject': subject,
                    'user_id': user_id
                }
            }), 404
        
        # Parse metadata from content if present
        metadata = {}
        content_lines = lesson_content.split('\n')
        if content_lines[0].strip() == '---':
            # Find end of metadata
            metadata_end = -1
            for i, line in enumerate(content_lines[1:], 1):
                if line.strip() == '---':
                    metadata_end = i
                    break
            
            if metadata_end > 0:
                # Parse metadata
                for line in content_lines[1:metadata_end]:
                    if ':' in line:
                        key, value = line.split(':', 1)
                        metadata[key.strip()] = value.strip()
                
                # Remove metadata from content
                lesson_content = '\n'.join(content_lines[metadata_end + 1:]).strip()
        
        logger.info(f"LangChain lesson {lesson_id} retrieved for {user_id} - {subject}")
        
        return jsonify({
            'success': True,
            'lesson': {
                'lesson_id': lesson_id,
                'user_id': user_id,
                'subject': subject,
                'content': lesson_content,
                'metadata': metadata,
                'generation_method': 'langchain',
                'retrieved_at': metadata.get('generated_at', 'unknown')
            }
        }), 200
        
    except ValueError as e:
        logger.warning(f"Validation error retrieving LangChain lesson: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'validation_error',
            'message': str(e)
        }), 400
        
    except Exception as e:
        logger.error(f"Error retrieving LangChain lesson {lesson_id} for {user_id} - {subject}: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'retrieval_error',
            'message': 'Failed to retrieve lesson'
        }), 500

@lessons_bp.route('/users/<user_id>/subjects/<subject>/lessons/pipeline-cancel/<pipeline_id>', methods=['POST'])
def cancel_pipeline(user_id, subject, pipeline_id):
    """Cancel a running LangChain pipeline"""
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
        
        logger.info(f"Cancelling pipeline {pipeline_id} for user {user_id}, subject {subject}")
        
        # Get pipeline progress to verify ownership
        orchestrator = get_pipeline_orchestrator()
        progress = orchestrator.get_pipeline_progress(pipeline_id)
        
        if not progress:
            logger.warning(f"Pipeline not found for cancellation: {pipeline_id}")
            return jsonify({
                'success': False,
                'error': 'not_found',
                'message': 'Pipeline not found',
                'pipeline_id': pipeline_id
            }), 404
        
        # Verify pipeline belongs to the user and subject
        if progress['user_id'] != user_id or progress['subject'] != subject:
            logger.warning(f"Pipeline cancellation access denied: {pipeline_id} for {user_id}/{subject}")
            return jsonify({
                'success': False,
                'error': 'access_denied',
                'message': 'Pipeline access denied'
            }), 403
        
        # Cancel the pipeline
        cancelled = orchestrator.cancel_pipeline(pipeline_id)
        
        if cancelled:
            logger.info(f"Pipeline {pipeline_id} cancelled successfully")
            return jsonify({
                'success': True,
                'message': 'Pipeline cancelled successfully',
                'pipeline_id': pipeline_id,
                'status': 'cancelled'
            }), 200
        else:
            logger.warning(f"Pipeline {pipeline_id} could not be cancelled (may already be completed)")
            return jsonify({
                'success': False,
                'error': 'cancellation_failed',
                'message': 'Pipeline could not be cancelled (may already be completed)',
                'pipeline_id': pipeline_id
            }), 400
        
    except ValueError as e:
        logger.warning(f"Validation error cancelling pipeline: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'validation_error',
            'message': str(e)
        }), 400
        
    except Exception as e:
        logger.error(f"Error cancelling pipeline {pipeline_id}: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'cancellation_error',
            'message': 'Failed to cancel pipeline'
        }), 500