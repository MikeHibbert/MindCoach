"""
API endpoints for testing LangChain infrastructure
"""
import logging
from flask import Blueprint, jsonify, request
from app.services.langchain_pipeline import LangChainPipelineService
from app.services.langchain_base import validate_environment, test_xai_connection

logger = logging.getLogger(__name__)

langchain_test_bp = Blueprint('langchain_test', __name__)

@langchain_test_bp.route('/test/langchain/status', methods=['GET'])
def get_langchain_status():
    """Get the status of LangChain pipeline components"""
    try:
        pipeline = LangChainPipelineService()
        status = pipeline.get_pipeline_status()
        
        return jsonify({
            'status': 'success',
            'pipeline_status': status
        }), 200
        
    except Exception as e:
        logger.error(f"Failed to get LangChain status: {e}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@langchain_test_bp.route('/test/langchain/connection', methods=['GET'])
def test_langchain_connection():
    """Test connection to xAI API"""
    try:
        pipeline = LangChainPipelineService()
        result = pipeline.test_connection()
        
        status_code = 200 if result['status'] == 'success' else 500
        
        return jsonify(result), status_code
        
    except Exception as e:
        logger.error(f"Connection test failed: {e}")
        return jsonify({
            'status': 'error',
            'message': str(e),
            'timestamp': '2024-01-15T10:00:00Z'
        }), 500

@langchain_test_bp.route('/test/langchain/environment', methods=['GET'])
def test_environment_validation():
    """Test environment variable validation"""
    try:
        validate_environment()
        
        return jsonify({
            'status': 'success',
            'message': 'Environment validation passed',
            'variables_checked': ['XAI_API_KEY', 'GROK_API_URL']
        }), 200
        
    except Exception as e:
        logger.error(f"Environment validation failed: {e}")
        return jsonify({
            'status': 'error',
            'message': str(e),
            'variables_checked': ['XAI_API_KEY', 'GROK_API_URL']
        }), 500

@langchain_test_bp.route('/test/langchain/survey', methods=['POST'])
def test_survey_generation():
    """Test survey generation with LangChain"""
    try:
        data = request.get_json()
        subject = data.get('subject', 'python')
        
        if not subject:
            return jsonify({
                'status': 'error',
                'message': 'Subject is required'
            }), 400
        
        pipeline = LangChainPipelineService()
        result = pipeline.generate_survey(subject)
        
        return jsonify({
            'status': 'success',
            'survey_data': result
        }), 200
        
    except Exception as e:
        logger.error(f"Survey generation test failed: {e}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@langchain_test_bp.route('/test/langchain/pipeline', methods=['POST'])
def test_full_pipeline():
    """Test the full three-stage pipeline (will show not implemented stages)"""
    try:
        data = request.get_json()
        subject = data.get('subject', 'python')
        survey_data = data.get('survey_data', {
            'answers': [{'question_id': 1, 'answer': 'A', 'correct': True}],
            'skill_level': 'intermediate'
        })
        
        pipeline = LangChainPipelineService()
        
        try:
            result = pipeline.run_full_pipeline(survey_data, subject)
            return jsonify({
                'status': 'success',
                'pipeline_result': result
            }), 200
            
        except NotImplementedError as e:
            return jsonify({
                'status': 'partial_success',
                'message': str(e),
                'implemented_stages': ['survey_generation'],
                'pending_stages': ['curriculum_generation', 'lesson_planning', 'content_generation']
            }), 200
        
    except Exception as e:
        logger.error(f"Full pipeline test failed: {e}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500