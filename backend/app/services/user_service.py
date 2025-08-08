"""
User service providing CRUD operations for User model
"""

from app.models.user import User
from app.services.database_service import DatabaseService
from sqlalchemy.exc import SQLAlchemyError
import logging

logger = logging.getLogger(__name__)

class UserService:
    """Service class for User model operations"""
    
    @staticmethod
    def create_user(user_id, email=None):
        """Create a new user"""
        try:
            with DatabaseService.transaction():
                # Check if user already exists
                existing_user = User.query.filter_by(user_id=user_id).first()
                if existing_user:
                    logger.warning(f"User {user_id} already exists")
                    return existing_user
                
                user = User(user_id=user_id, email=email)
                DatabaseService.get_session().add(user)
                logger.info(f"Created user: {user_id}")
                return user
        except SQLAlchemyError as e:
            logger.error(f"Failed to create user {user_id}: {str(e)}")
            raise
    
    @staticmethod
    def get_user_by_id(user_id):
        """Get user by user_id"""
        try:
            return User.query.filter_by(user_id=user_id).first()
        except SQLAlchemyError as e:
            logger.error(f"Failed to get user {user_id}: {str(e)}")
            raise
    
    @staticmethod
    def get_user_by_pk(pk):
        """Get user by primary key"""
        try:
            return User.query.get(pk)
        except SQLAlchemyError as e:
            logger.error(f"Failed to get user by pk {pk}: {str(e)}")
            raise
    
    @staticmethod
    def update_user(user_id, **kwargs):
        """Update user information"""
        try:
            with DatabaseService.transaction():
                user = User.query.filter_by(user_id=user_id).first()
                if not user:
                    logger.warning(f"User {user_id} not found for update")
                    return None
                
                for key, value in kwargs.items():
                    if hasattr(user, key):
                        setattr(user, key, value)
                
                logger.info(f"Updated user: {user_id}")
                return user
        except SQLAlchemyError as e:
            logger.error(f"Failed to update user {user_id}: {str(e)}")
            raise
    
    @staticmethod
    def delete_user(user_id):
        """Delete a user"""
        try:
            with DatabaseService.transaction():
                user = User.query.filter_by(user_id=user_id).first()
                if not user:
                    logger.warning(f"User {user_id} not found for deletion")
                    return False
                
                DatabaseService.get_session().delete(user)
                logger.info(f"Deleted user: {user_id}")
                return True
        except SQLAlchemyError as e:
            logger.error(f"Failed to delete user {user_id}: {str(e)}")
            raise
    
    @staticmethod
    def get_all_users():
        """Get all users"""
        try:
            return User.query.all()
        except SQLAlchemyError as e:
            logger.error(f"Failed to get all users: {str(e)}")
            raise
    
    @staticmethod
    def user_exists(user_id):
        """Check if user exists"""
        try:
            return User.query.filter_by(user_id=user_id).first() is not None
        except SQLAlchemyError as e:
            logger.error(f"Failed to check if user {user_id} exists: {str(e)}")
            raise