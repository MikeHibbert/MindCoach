"""
Survey result service providing CRUD operations for SurveyResult model
"""

from app.models.survey_result import SurveyResult
from app.services.database_service import DatabaseService
from sqlalchemy.exc import SQLAlchemyError
import logging

logger = logging.getLogger(__name__)

class SurveyResultService:
    """Service class for SurveyResult model operations"""
    
    @staticmethod
    def create_survey_result(user_id, subject, skill_level):
        """Create a new survey result"""
        try:
            with DatabaseService.transaction():
                # Check if survey result already exists for this user/subject
                existing_result = SurveyResultService.get_survey_result(user_id, subject)
                if existing_result:
                    logger.info(f"Updating existing survey result for {user_id} - {subject}")
                    return SurveyResultService.update_survey_result(
                        user_id, subject, skill_level=skill_level
                    )
                
                survey_result = SurveyResult(
                    user_id=user_id,
                    subject=subject,
                    skill_level=skill_level
                )
                DatabaseService.get_session().add(survey_result)
                logger.info(f"Created survey result: {user_id} - {subject} - {skill_level}")
                return survey_result
        except SQLAlchemyError as e:
            logger.error(f"Failed to create survey result for {user_id} - {subject}: {str(e)}")
            raise
    
    @staticmethod
    def get_survey_result(user_id, subject):
        """Get survey result by user_id and subject"""
        try:
            return SurveyResult.query.filter_by(
                user_id=user_id, subject=subject
            ).first()
        except SQLAlchemyError as e:
            logger.error(f"Failed to get survey result for {user_id} - {subject}: {str(e)}")
            raise
    
    @staticmethod
    def get_user_survey_results(user_id):
        """Get all survey results for a user"""
        try:
            return SurveyResult.query.filter_by(user_id=user_id).all()
        except SQLAlchemyError as e:
            logger.error(f"Failed to get survey results for user {user_id}: {str(e)}")
            raise
    
    @staticmethod
    def get_survey_result_by_pk(pk):
        """Get survey result by primary key"""
        try:
            return SurveyResult.query.get(pk)
        except SQLAlchemyError as e:
            logger.error(f"Failed to get survey result by pk {pk}: {str(e)}")
            raise
    
    @staticmethod
    def update_survey_result(user_id, subject, **kwargs):
        """Update survey result information"""
        try:
            with DatabaseService.transaction():
                survey_result = SurveyResult.query.filter_by(
                    user_id=user_id, subject=subject
                ).first()
                
                if not survey_result:
                    logger.warning(f"Survey result for {user_id} - {subject} not found for update")
                    return None
                
                for key, value in kwargs.items():
                    if hasattr(survey_result, key):
                        setattr(survey_result, key, value)
                
                logger.info(f"Updated survey result: {user_id} - {subject}")
                return survey_result
        except SQLAlchemyError as e:
            logger.error(f"Failed to update survey result for {user_id} - {subject}: {str(e)}")
            raise
    
    @staticmethod
    def delete_survey_result(user_id, subject):
        """Delete a survey result"""
        try:
            with DatabaseService.transaction():
                survey_result = SurveyResult.query.filter_by(
                    user_id=user_id, subject=subject
                ).first()
                
                if not survey_result:
                    logger.warning(f"Survey result for {user_id} - {subject} not found for deletion")
                    return False
                
                DatabaseService.get_session().delete(survey_result)
                logger.info(f"Deleted survey result: {user_id} - {subject}")
                return True
        except SQLAlchemyError as e:
            logger.error(f"Failed to delete survey result for {user_id} - {subject}: {str(e)}")
            raise
    
    @staticmethod
    def get_all_survey_results():
        """Get all survey results"""
        try:
            return SurveyResult.query.all()
        except SQLAlchemyError as e:
            logger.error(f"Failed to get all survey results: {str(e)}")
            raise
    
    @staticmethod
    def get_results_by_skill_level(skill_level):
        """Get all survey results by skill level"""
        try:
            return SurveyResult.query.filter_by(skill_level=skill_level).all()
        except SQLAlchemyError as e:
            logger.error(f"Failed to get survey results by skill level {skill_level}: {str(e)}")
            raise
    
    @staticmethod
    def get_results_by_subject(subject):
        """Get all survey results for a specific subject"""
        try:
            return SurveyResult.query.filter_by(subject=subject).all()
        except SQLAlchemyError as e:
            logger.error(f"Failed to get survey results for subject {subject}: {str(e)}")
            raise