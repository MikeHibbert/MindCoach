from flask import Blueprint, request, jsonify
import logging

from app.services.langchain_pipeline import LangChainPipelineService
from app.services.survey_analysis_service import SurveyAnalysisService
from app.services.file_service import FileService
from app.utils.validation import validate_user_id, validate_subject

logger = logging.getLogger(__name__)

surveys_bp = Blueprint('surveys', __name__)

@surveys_bp.route('/users/<user_id>/subjects/<subject>/survey/generate', methods=['POST'])
def generate_survey(user_id, subject):
    """Generate a new survey for a user and subject using LangChain"""
    try:
        # Validate input parameters
        validate_user_id(user_id)
        validate_subject(subject)
        
        logger.info(f"Generating LangChain-powered survey for user {user_id}, subject {subject}")
        
        # Initialize LangChain pipeline
        pipeline = LangChainPipelineService()
        
        # Load RAG documents for survey generation
        rag_docs = pipeline.survey_chain.load_rag_documents('survey', subject)
        
        # Generate the survey using LangChain
        try:
            survey_data = pipeline.generate_survey(subject, rag_docs)
        except ValueError as e:
            if "Invalid JSON" in str(e):
                logger.error(f"JSON parsing error during survey generation: {e}")
                return jsonify({
                    'success': False,
                    'error': 'generation_error',
                    'message': 'Survey generation failed due to response formatting issues. Please try again.',
                    'details': 'The AI response could not be parsed properly. This is usually temporary.'
                }), 500
            else:
                raise e
        
        # Add user-specific metadata
        survey_data['user_id'] = user_id
        
        # Validate survey structure
        if not _validate_survey_structure(survey_data):
            raise ValueError("Generated survey does not meet quality standards")
        
        # Save survey to file system
        file_path = f"users/{user_id}/{subject}/survey.json"
        FileService.save_json(file_path, survey_data)
        
        logger.info(f"LangChain survey generated and saved for {user_id} - {subject}")
        
        # Return survey without correct answers for security
        response_survey = survey_data.copy()
        for question in response_survey['questions']:
            question.pop('correct_answer', None)
        
        return jsonify({
            'success': True,
            'survey': response_survey,
            'message': f'AI-powered survey generated successfully for {subject}',
            'generation_method': 'langchain'
        }), 201
        
    except ValueError as e:
        logger.warning(f"Validation error generating survey: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'validation_error',
            'message': str(e)
        }), 400
        
    except Exception as e:
        logger.error(f"Error generating LangChain survey for {user_id} - {subject}: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'generation_error',
            'message': 'Failed to generate AI-powered survey'
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

def _validate_survey_structure(survey: dict) -> bool:
    """
    Validate that a LangChain-generated survey meets quality standards
    
    Args:
        survey: Survey dictionary to validate
        
    Returns:
        True if valid, False otherwise
    """
    try:
        # Check required top-level fields
        required_fields = ['questions', 'total_questions', 'subject']
        for field in required_fields:
            if field not in survey:
                logger.error(f"Survey missing required field: {field}")
                return False
        
        # Check questions structure
        questions = survey.get('questions', [])
        if not isinstance(questions, list) or len(questions) == 0:
            logger.error("Survey must have a non-empty list of questions")
            return False
        
        # Validate question count
        if len(questions) < 5 or len(questions) > 10:
            logger.error(f"Survey must have 5-10 questions, got {len(questions)}")
            return False
        
        # Validate each question
        for i, question in enumerate(questions):
            if not _validate_question_structure(question, i + 1):
                return False
        
        # Check difficulty distribution
        if not _validate_difficulty_distribution(questions):
            return False
        
        logger.info(f"Survey validation passed: {len(questions)} questions")
        return True
        
    except Exception as e:
        logger.error(f"Error validating survey structure: {e}")
        return False

def _validate_question_structure(question: dict, question_num: int) -> bool:
    """Validate individual question structure"""
    required_fields = ['id', 'question', 'type', 'options', 'correct_answer', 'difficulty', 'topic']
    
    for field in required_fields:
        if field not in question:
            logger.error(f"Question {question_num} missing required field: {field}")
            return False
    
    # Validate question type
    if question['type'] != 'multiple_choice':
        logger.error(f"Question {question_num} must be multiple_choice type")
        return False
    
    # Validate options
    options = question.get('options', [])
    if not isinstance(options, list) or len(options) != 4:
        logger.error(f"Question {question_num} must have exactly 4 options")
        return False
    
    # Validate correct answer
    correct_answer = question.get('correct_answer')
    if correct_answer not in options:
        logger.error(f"Question {question_num} correct_answer must be one of the options")
        return False
    
    # Validate difficulty
    valid_difficulties = ['beginner', 'intermediate', 'advanced']
    if question.get('difficulty') not in valid_difficulties:
        logger.error(f"Question {question_num} difficulty must be one of: {valid_difficulties}")
        return False
    
    return True

def _validate_difficulty_distribution(questions: list) -> bool:
    """Validate that difficulty distribution meets guidelines"""
    difficulty_counts = {'beginner': 0, 'intermediate': 0, 'advanced': 0}
    
    for question in questions:
        difficulty = question.get('difficulty')
        if difficulty in difficulty_counts:
            difficulty_counts[difficulty] += 1
    
    total_questions = len(questions)
    
    # Check minimum requirements (based on RAG guidelines)
    beginner_pct = difficulty_counts['beginner'] / total_questions
    intermediate_pct = difficulty_counts['intermediate'] / total_questions
    advanced_pct = difficulty_counts['advanced'] / total_questions
    
    # Beginner: 30-40%
    if beginner_pct < 0.25 or beginner_pct > 0.5:
        logger.warning(f"Beginner questions: {beginner_pct:.1%} (recommended: 30-40%)")
    
    # Intermediate: 40-50%
    if intermediate_pct < 0.3 or intermediate_pct > 0.6:
        logger.warning(f"Intermediate questions: {intermediate_pct:.1%} (recommended: 40-50%)")
    
    # Advanced: 20-30%
    if advanced_pct < 0.1 or advanced_pct > 0.4:
        logger.warning(f"Advanced questions: {advanced_pct:.1%} (recommended: 20-30%)")
    
    # Ensure we have at least one question of each difficulty
    if difficulty_counts['beginner'] == 0:
        logger.error("Survey must have at least one beginner question")
        return False
    
    if difficulty_counts['intermediate'] == 0:
        logger.error("Survey must have at least one intermediate question")
        return False
    
    logger.info(f"Difficulty distribution: B:{difficulty_counts['beginner']} I:{difficulty_counts['intermediate']} A:{difficulty_counts['advanced']}")
    return True