"""
Session management service for horizontal scaling
Handles distributed sessions using Redis
"""

import json
import uuid
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
import redis
from flask import current_app
import logging

logger = logging.getLogger(__name__)


class SessionService:
    """Distributed session management service"""
    
    def __init__(self, redis_client: Optional[redis.Redis] = None):
        self.redis_client = redis_client or self._get_redis_client()
        self.session_prefix = "session:"
        self.default_ttl = 3600 * 24  # 24 hours
    
    def _get_redis_client(self) -> redis.Redis:
        """Get Redis client from Flask app config"""
        redis_url = current_app.config.get('REDIS_URL', 'redis://localhost:6379/0')
        return redis.from_url(redis_url, decode_responses=True)
    
    def create_session(self, user_id: str, data: Optional[Dict[str, Any]] = None) -> str:
        """
        Create a new session
        
        Args:
            user_id: User identifier
            data: Optional session data
            
        Returns:
            Session ID
        """
        try:
            session_id = str(uuid.uuid4())
            session_data = {
                'user_id': user_id,
                'created_at': datetime.utcnow().isoformat(),
                'updated_at': datetime.utcnow().isoformat(),
                'data': data or {}
            }
            
            # Store in Redis with TTL
            key = f"{self.session_prefix}{session_id}"
            self.redis_client.setex(
                key, 
                self.default_ttl, 
                json.dumps(session_data)
            )
            
            # Also store user -> session mapping for cleanup
            user_key = f"user_sessions:{user_id}"
            self.redis_client.sadd(user_key, session_id)
            self.redis_client.expire(user_key, self.default_ttl)
            
            logger.info(f"Created session {session_id} for user {user_id}")
            return session_id
            
        except Exception as e:
            logger.error(f"Failed to create session for user {user_id}: {e}")
            raise
    
    def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """
        Get session data
        
        Args:
            session_id: Session identifier
            
        Returns:
            Session data or None if not found
        """
        try:
            key = f"{self.session_prefix}{session_id}"
            data = self.redis_client.get(key)
            
            if data:
                session_data = json.loads(data)
                # Update last accessed time
                session_data['last_accessed'] = datetime.utcnow().isoformat()
                self.redis_client.setex(key, self.default_ttl, json.dumps(session_data))
                return session_data
            
            return None
            
        except Exception as e:
            logger.error(f"Failed to get session {session_id}: {e}")
            return None
    
    def update_session(self, session_id: str, data: Dict[str, Any]) -> bool:
        """
        Update session data
        
        Args:
            session_id: Session identifier
            data: Data to update
            
        Returns:
            True if successful, False otherwise
        """
        try:
            key = f"{self.session_prefix}{session_id}"
            existing_data = self.redis_client.get(key)
            
            if not existing_data:
                logger.warning(f"Session {session_id} not found for update")
                return False
            
            session_data = json.loads(existing_data)
            session_data['data'].update(data)
            session_data['updated_at'] = datetime.utcnow().isoformat()
            
            self.redis_client.setex(key, self.default_ttl, json.dumps(session_data))
            logger.debug(f"Updated session {session_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to update session {session_id}: {e}")
            return False
    
    def delete_session(self, session_id: str) -> bool:
        """
        Delete a session
        
        Args:
            session_id: Session identifier
            
        Returns:
            True if successful, False otherwise
        """
        try:
            key = f"{self.session_prefix}{session_id}"
            
            # Get session data to find user_id
            data = self.redis_client.get(key)
            if data:
                session_data = json.loads(data)
                user_id = session_data.get('user_id')
                
                # Remove from user sessions set
                if user_id:
                    user_key = f"user_sessions:{user_id}"
                    self.redis_client.srem(user_key, session_id)
            
            # Delete the session
            result = self.redis_client.delete(key)
            logger.info(f"Deleted session {session_id}")
            return result > 0
            
        except Exception as e:
            logger.error(f"Failed to delete session {session_id}: {e}")
            return False
    
    def delete_user_sessions(self, user_id: str) -> int:
        """
        Delete all sessions for a user
        
        Args:
            user_id: User identifier
            
        Returns:
            Number of sessions deleted
        """
        try:
            user_key = f"user_sessions:{user_id}"
            session_ids = self.redis_client.smembers(user_key)
            
            deleted_count = 0
            for session_id in session_ids:
                if self.delete_session(session_id):
                    deleted_count += 1
            
            # Clean up user sessions set
            self.redis_client.delete(user_key)
            
            logger.info(f"Deleted {deleted_count} sessions for user {user_id}")
            return deleted_count
            
        except Exception as e:
            logger.error(f"Failed to delete sessions for user {user_id}: {e}")
            return 0
    
    def extend_session(self, session_id: str, ttl: Optional[int] = None) -> bool:
        """
        Extend session TTL
        
        Args:
            session_id: Session identifier
            ttl: Time to live in seconds (default: default_ttl)
            
        Returns:
            True if successful, False otherwise
        """
        try:
            key = f"{self.session_prefix}{session_id}"
            ttl = ttl or self.default_ttl
            
            if self.redis_client.exists(key):
                self.redis_client.expire(key, ttl)
                logger.debug(f"Extended session {session_id} TTL to {ttl} seconds")
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Failed to extend session {session_id}: {e}")
            return False
    
    def get_active_sessions_count(self, user_id: Optional[str] = None) -> int:
        """
        Get count of active sessions
        
        Args:
            user_id: Optional user identifier to filter by
            
        Returns:
            Number of active sessions
        """
        try:
            if user_id:
                user_key = f"user_sessions:{user_id}"
                return self.redis_client.scard(user_key)
            else:
                # Count all session keys
                pattern = f"{self.session_prefix}*"
                return len(self.redis_client.keys(pattern))
                
        except Exception as e:
            logger.error(f"Failed to get active sessions count: {e}")
            return 0
    
    def cleanup_expired_sessions(self) -> int:
        """
        Clean up expired sessions (Redis handles this automatically with TTL)
        This method is for manual cleanup if needed
        
        Returns:
            Number of sessions cleaned up
        """
        try:
            pattern = f"{self.session_prefix}*"
            keys = self.redis_client.keys(pattern)
            
            cleaned_count = 0
            for key in keys:
                # Check if key exists (Redis may have already expired it)
                if not self.redis_client.exists(key):
                    cleaned_count += 1
            
            logger.info(f"Cleaned up {cleaned_count} expired sessions")
            return cleaned_count
            
        except Exception as e:
            logger.error(f"Failed to cleanup expired sessions: {e}")
            return 0
    
    def get_session_stats(self) -> Dict[str, Any]:
        """
        Get session statistics
        
        Returns:
            Dictionary with session statistics
        """
        try:
            total_sessions = self.get_active_sessions_count()
            
            # Get Redis memory usage
            info = self.redis_client.info('memory')
            memory_usage = info.get('used_memory_human', 'Unknown')
            
            # Get Redis connection count
            clients_info = self.redis_client.info('clients')
            connected_clients = clients_info.get('connected_clients', 0)
            
            return {
                'total_active_sessions': total_sessions,
                'redis_memory_usage': memory_usage,
                'redis_connected_clients': connected_clients,
                'session_prefix': self.session_prefix,
                'default_ttl': self.default_ttl,
                'timestamp': datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Failed to get session stats: {e}")
            return {
                'error': str(e),
                'timestamp': datetime.utcnow().isoformat()
            }


# Global session service instance
session_service = SessionService()


def get_session_service() -> SessionService:
    """Get the global session service instance"""
    return session_service