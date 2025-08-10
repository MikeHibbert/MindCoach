"""
Cache Service for Backend API Performance Optimization
"""
import json
import time
from typing import Any, Optional, Dict, Callable
from functools import wraps
import hashlib
import logging

logger = logging.getLogger(__name__)

class InMemoryCache:
    """Simple in-memory cache with TTL support"""
    
    def __init__(self):
        self._cache: Dict[str, Dict[str, Any]] = {}
        self._default_ttl = 300  # 5 minutes default
    
    def get(self, key: str) -> Optional[Any]:
        """Get value from cache if not expired"""
        if key not in self._cache:
            return None
        
        entry = self._cache[key]
        if time.time() > entry['expires_at']:
            del self._cache[key]
            return None
        
        entry['last_accessed'] = time.time()
        return entry['value']
    
    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        """Set value in cache with TTL"""
        if ttl is None:
            ttl = self._default_ttl
        
        self._cache[key] = {
            'value': value,
            'expires_at': time.time() + ttl,
            'created_at': time.time(),
            'last_accessed': time.time()
        }
    
    def delete(self, key: str) -> bool:
        """Delete key from cache"""
        if key in self._cache:
            del self._cache[key]
            return True
        return False
    
    def clear(self) -> None:
        """Clear all cache entries"""
        self._cache.clear()
    
    def cleanup_expired(self) -> int:
        """Remove expired entries and return count"""
        current_time = time.time()
        expired_keys = [
            key for key, entry in self._cache.items()
            if current_time > entry['expires_at']
        ]
        
        for key in expired_keys:
            del self._cache[key]
        
        return len(expired_keys)
    
    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        current_time = time.time()
        total_entries = len(self._cache)
        expired_entries = sum(
            1 for entry in self._cache.values()
            if current_time > entry['expires_at']
        )
        
        return {
            'total_entries': total_entries,
            'active_entries': total_entries - expired_entries,
            'expired_entries': expired_entries,
            'memory_usage_estimate': sum(
                len(str(entry['value'])) for entry in self._cache.values()
            )
        }

# Global cache instance
cache = InMemoryCache()

def cache_key(*args, **kwargs) -> str:
    """Generate cache key from arguments"""
    key_data = {
        'args': args,
        'kwargs': sorted(kwargs.items())
    }
    key_string = json.dumps(key_data, sort_keys=True, default=str)
    return hashlib.md5(key_string.encode()).hexdigest()

def cached(ttl: int = 300, key_prefix: str = ''):
    """Decorator to cache function results"""
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Generate cache key
            func_key = f"{key_prefix}:{func.__name__}:{cache_key(*args, **kwargs)}"
            
            # Try to get from cache
            cached_result = cache.get(func_key)
            if cached_result is not None:
                logger.debug(f"Cache hit for {func.__name__}")
                return cached_result
            
            # Execute function and cache result
            try:
                result = func(*args, **kwargs)
                cache.set(func_key, result, ttl)
                logger.debug(f"Cache miss for {func.__name__}, result cached")
                return result
            except Exception as e:
                logger.error(f"Error in cached function {func.__name__}: {e}")
                raise
        
        # Add cache management methods to function
        wrapper.cache_clear = lambda: cache.clear()
        wrapper.cache_delete = lambda *args, **kwargs: cache.delete(
            f"{key_prefix}:{func.__name__}:{cache_key(*args, **kwargs)}"
        )
        
        return wrapper
    return decorator

def invalidate_cache_pattern(pattern: str) -> int:
    """Invalidate cache entries matching pattern"""
    keys_to_delete = [
        key for key in cache._cache.keys()
        if pattern in key
    ]
    
    for key in keys_to_delete:
        cache.delete(key)
    
    return len(keys_to_delete)

# Cache TTL constants
class CacheTTL:
    SHORT = 60      # 1 minute
    MEDIUM = 300    # 5 minutes
    LONG = 900      # 15 minutes
    VERY_LONG = 3600  # 1 hour

# Cache key prefixes
class CacheKeys:
    USER = 'user'
    SUBSCRIPTION = 'subscription'
    SURVEY = 'survey'
    LESSON = 'lesson'
    SUBJECT = 'subject'