from flask import Blueprint, request, jsonify
import logging

from app.services.survey_generation_service import SurveyGenerationService
from app.services.survey_analysis_service import SurveyAnalysisService
from app.services.file_service import FileService
from app.utils.validation import validate_user_id, validate_subject

logger = logging.getLogger(__name__)

surveys_bp = Blueprint('surveys', __name__)

@surveys_bp.route('/users/<user_id>/subjects/<subject>/survey/generate', methods=['POST'])
def generate_survey(user_id, subject):
    """Generate a new survey for a user and subject"""
    try:
        # Validate input parameters
        validate_user_id(user_id)
        validate_subject(subject)
        
        logger.info(f"Generating survey for user {user_id}, subject {subject}")
        
        # Generate the survey
        survey = SurveyGenerationService.generate_survey(subject, user_id)
        
        # Save survey to file system
        file_path = f"users/{user_id}/{subject}/survey.json"
        FileService.save_json(file_path, survey)
        
        logger.info(f"Survey generated and saved for {user_id} - {subject}")
        
        # Return survey without correct answers for security
        response_survey = survey.copy()
        for question in response_survey['questions']:
            question.pop('correct_answer', None)
        
        return jsonify({
            'success': True,
            'survey': response_survey,
            'message': f'Survey generated successfully for {subject}'
        }), 201
        
    except ValueError as e:
        logger.warning(f"Validation error generating survey: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'validation_error',
            'message': str(e)
        }), 400
        
    except Exception as e:
        logger.error(f"Error generating survey for {user_id} - {subject}: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'generation_error',
            'message': 'Failed to generate survey'
        }), 500

@surveys_bp.route('/users/<user_id>/subjects/<subject>/survey', methods=['GET'])
def get_survey(user_id, subject):
    """Retrieve an existing survey for a user and subject"""
    try:
        # Validate input parameters
        validate_user_id(user_id)
        validate_subject(subject)
        
        logger.info(f"Retrieving survey for user {user_id}, subject {subject}")
        
        # Load survey from file system
        file_path = f"users/{user_id}/{subject}/survey.json"
        survey = FileService.load_json(file_path)
        
        if not survey:
            logger.info(f"No survey found for {user_id} - {subject}")
            return jsonify({
                'success': False,
                'error': 'not_found',
                'message': 'Survey not found'
            }), 404
        
        # Remove correct answers for security
        response_survey = survey.copy()
        for question in response_survey['questions']:
            question.pop('correct_answer', None)
        
        logger.info(f"Survey retrieved for {user_id} - {subject}")
        return jsonify({
            'success': True,
            'survey': response_survey
        }), 200
        
    except ValueError as e:
        logger.warning(f"Validation error retrieving survey: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'validation_error',
            'message': str(e)
        }), 400
        
    except Exception as e:
        logger.error(f"Error retrieving survey for {user_id} - {subject}: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'retrieval_error',
            'message': 'Failed to retrieve survey'
        }), 500

@surveys_bp.route('/users/<user_id>/subjects/<subject>/survey/submit', methods=['POST'])
def submit_survey(user_id, subject):
    """Submit survey answers and get analysis results"""
    try:
        # Validate input parameters
        validate_user_id(user_id)
        validate_subject(subject)
        
        # Get request data
        data = request.get_json()
        if not data:
            return jsonify({
                'success': False,
                'error': 'validation_error',
                'message': 'Request body must contain JSON data'
            }), 400
        
        answers = data.get('answers')
        if not answers:
            return jsonify({
                'success': False,
                'error': 'validation_error',
                'message': 'Answers are required'
            }), 400
        
        logger.info(f"Processing survey submission for user {user_id}, subject {subject}")
        
        # Process the survey answers
        analysis_results = SurveyAnalysisService.process_survey_answers(
            user_id, subject, answers
        )
        
        logger.info(f"Survey processed for {user_id} - {subject}, skill level: {analysis_results['skill_level']}")
        
        # Return analysis results (without detailed processed answers for brevity)
        response_data = {
            'success': True,
            'results': {
                'user_id': analysis_results['user_id'],
                'subject': analysis_results['subject'],
                'skill_level': analysis_results['skill_level'],
                'accuracy': analysis_results['accuracy'],
                'total_questions': analysis_results['total_questions'],
                'correct_answers': analysis_results['correct_answers'],
                'topic_analysis': analysis_results['topic_analysis'],
                'recommendations': analysis_results['recommendations'],
                'processed_at': analysis_results['processed_at']
            },
            'message': f'Survey processed successfully. Skill level: {analysis_results["skill_level"]}'
        }
        
        return jsonify(response_data), 200
        
    except ValueError as e:
        logger.warning(f"Validation error submitting survey: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'validation_error',
            'message': str(e)
        }), 400
        
    except FileNotFoundError as e:
        logger.warning(f"Survey not found for submission: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'not_found',
            'message': 'Survey not found. Please generate a survey first.'
        }), 404
        
    except Exception as e:
        logger.error(f"Error processing survey submission for {user_id} - {subject}: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'processing_error',
            'message': 'Failed to process survey submission'
        }), 500

@surveys_bp.route('/users/<user_id>/subjects/<subject>/survey/results', methods=['GET'])
def get_survey_results(user_id, subject):
    """Retrieve survey analysis results for a user and subject"""
    try:
        # Validate input parameters
        validate_user_id(user_id)
        validate_subject(subject)
        
        logger.info(f"Retrieving survey results for user {user_id}, subject {subject}")
        
        # Get survey results
        results = SurveyAnalysisService.get_survey_results(user_id, subject)
        
        if not results:
            logger.info(f"No survey results found for {user_id} - {subject}")
            return jsonify({
                'success': False,
                'error': 'not_found',
                'message': 'Survey results not found'
            }), 404
        
        # Return results (without detailed processed answers for brevity)
        response_data = {
            'success': True,
            'results': {
                'user_id': results['user_id'],
                'subject': results['subject'],
                'skill_level': results['skill_level'],
                'accuracy': results['accuracy'],
                'total_questions': results['total_questions'],
                'correct_answers': results['correct_answers'],
                'topic_analysis': results['topic_analysis'],
                'recommendations': results['recommendations'],
                'processed_at': results['processed_at']
            }
        }
        
        logger.info(f"Survey results retrieved for {user_id} - {subject}")
        return jsonify(response_data), 200
        
    except ValueError as e:
        logger.warning(f"Validation error retrieving survey results: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'validation_error',
            'message': str(e)
        }), 400
        
    except Exception as e:
        logger.error(f"Error retrieving survey results for {user_id} - {subject}: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'retrieval_error',
            'message': 'Failed to retrieve survey results'
        }), 500