"""
Subscription service providing CRUD operations for Subscription model
"""

from app.models.subscription import Subscription
from app.services.database_service import DatabaseService
from sqlalchemy.exc import SQLAlchemyError
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class SubscriptionService:
    """Service class for Subscription model operations"""
    
    @staticmethod
    def create_subscription(user_id, subject, status='active', expires_at=None):
        """Create a new subscription"""
        try:
            with DatabaseService.transaction():
                # Check if subscription already exists
                existing_sub = Subscription.query.filter_by(
                    user_id=user_id, subject=subject
                ).first()
                
                if existing_sub:
                    logger.warning(f"Subscription for user {user_id} and subject {subject} already exists")
                    return existing_sub
                
                subscription = Subscription(
                    user_id=user_id,
                    subject=subject,
                    status=status,
                    expires_at=expires_at
                )
                DatabaseService.get_session().add(subscription)
                logger.info(f"Created subscription: {user_id} - {subject}")
                return subscription
        except SQLAlchemyError as e:
            logger.error(f"Failed to create subscription for {user_id} - {subject}: {str(e)}")
            raise
    
    @staticmethod
    def get_subscription(user_id, subject):
        """Get subscription by user_id and subject"""
        try:
            return Subscription.query.filter_by(
                user_id=user_id, subject=subject
            ).first()
        except SQLAlchemyError as e:
            logger.error(f"Failed to get subscription for {user_id} - {subject}: {str(e)}")
            raise
    
    @staticmethod
    def get_user_subscriptions(user_id):
        """Get all subscriptions for a user"""
        try:
            return Subscription.query.filter_by(user_id=user_id).all()
        except SQLAlchemyError as e:
            logger.error(f"Failed to get subscriptions for user {user_id}: {str(e)}")
            raise
    
    @staticmethod
    def get_active_subscriptions(user_id):
        """Get all active subscriptions for a user"""
        try:
            now = datetime.utcnow()
            return Subscription.query.filter_by(
                user_id=user_id, status='active'
            ).filter(
                (Subscription.expires_at.is_(None)) | 
                (Subscription.expires_at > now)
            ).all()
        except SQLAlchemyError as e:
            logger.error(f"Failed to get active subscriptions for user {user_id}: {str(e)}")
            raise
    
    @staticmethod
    def update_subscription(user_id, subject, **kwargs):
        """Update subscription information"""
        try:
            with DatabaseService.transaction():
                subscription = Subscription.query.filter_by(
                    user_id=user_id, subject=subject
                ).first()
                
                if not subscription:
                    logger.warning(f"Subscription for {user_id} - {subject} not found for update")
                    return None
                
                for key, value in kwargs.items():
                    if hasattr(subscription, key):
                        setattr(subscription, key, value)
                
                logger.info(f"Updated subscription: {user_id} - {subject}")
                return subscription
        except SQLAlchemyError as e:
            logger.error(f"Failed to update subscription for {user_id} - {subject}: {str(e)}")
            raise
    
    @staticmethod
    def cancel_subscription(user_id, subject):
        """Cancel a subscription (set status to cancelled)"""
        try:
            return SubscriptionService.update_subscription(
                user_id, subject, status='cancelled'
            )
        except SQLAlchemyError as e:
            logger.error(f"Failed to cancel subscription for {user_id} - {subject}: {str(e)}")
            raise
    
    @staticmethod
    def delete_subscription(user_id, subject):
        """Delete a subscription"""
        try:
            with DatabaseService.transaction():
                subscription = Subscription.query.filter_by(
                    user_id=user_id, subject=subject
                ).first()
                
                if not subscription:
                    logger.warning(f"Subscription for {user_id} - {subject} not found for deletion")
                    return False
                
                DatabaseService.get_session().delete(subscription)
                logger.info(f"Deleted subscription: {user_id} - {subject}")
                return True
        except SQLAlchemyError as e:
            logger.error(f"Failed to delete subscription for {user_id} - {subject}: {str(e)}")
            raise
    
    @staticmethod
    def has_active_subscription(user_id, subject):
        """Check if user has active subscription for subject"""
        try:
            now = datetime.utcnow()
            subscription = Subscription.query.filter_by(
                user_id=user_id, subject=subject, status='active'
            ).filter(
                (Subscription.expires_at.is_(None)) | 
                (Subscription.expires_at > now)
            ).first()
            
            return subscription is not None
        except SQLAlchemyError as e:
            logger.error(f"Failed to check subscription status for {user_id} - {subject}: {str(e)}")
            raise
    
    @staticmethod
    def get_expired_subscriptions():
        """Get all expired subscriptions"""
        try:
            now = datetime.utcnow()
            return Subscription.query.filter(
                Subscription.expires_at < now,
                Subscription.status == 'active'
            ).all()
        except SQLAlchemyError as e:
            logger.error(f"Failed to get expired subscriptions: {str(e)}")
            raise