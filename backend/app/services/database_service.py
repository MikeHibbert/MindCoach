"""
Database service layer providing connection management and base CRUD operations
"""

from app import db
from sqlalchemy.exc import SQLAlchemyError
from contextlib import contextmanager
import logging

logger = logging.getLogger(__name__)

class DatabaseService:
    """Base database service with connection and transaction management"""
    
    @staticmethod
    @contextmanager
    def transaction():
        """Context manager for database transactions with automatic rollback on error"""
        try:
            yield db.session
            db.session.commit()
        except SQLAlchemyError as e:
            db.session.rollback()
            logger.error(f"Database transaction failed: {str(e)}")
            raise
        except Exception as e:
            db.session.rollback()
            logger.error(f"Unexpected error in database transaction: {str(e)}")
            raise
    
    @staticmethod
    def safe_commit():
        """Safely commit changes with error handling"""
        try:
            db.session.commit()
            return True
        except SQLAlchemyError as e:
            db.session.rollback()
            logger.error(f"Database commit failed: {str(e)}")
            return False
    
    @staticmethod
    def safe_rollback():
        """Safely rollback changes"""
        try:
            db.session.rollback()
        except SQLAlchemyError as e:
            logger.error(f"Database rollback failed: {str(e)}")
    
    @staticmethod
    def get_session():
        """Get current database session"""
        return db.session