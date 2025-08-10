/**
 * Cache Service for optimizing API calls and data storage
 */
class CacheService {
  constructor() {
    this.cache = new Map();
    this.cacheExpiry = new Map();
    this.defaultTTL = 5 * 60 * 1000; // 5 minutes default TTL
  }

  /**
   * Set cache with TTL
   */
  set(key, value, ttl = this.defaultTTL) {
    this.cache.set(key, value);
    this.cacheExpiry.set(key, Date.now() + ttl);
    
    // Clean up expired entries periodically
    this.cleanupExpired();
  }

  /**
   * Get cached value if not expired
   */
  get(key) {
    const expiry = this.cacheExpiry.get(key);
    
    if (!expiry || Date.now() > expiry) {
      this.delete(key);
      return null;
    }
    
    return this.cache.get(key);
  }

  /**
   * Delete cache entry
   */
  delete(key) {
    this.cache.delete(key);
    this.cacheExpiry.delete(key);
  }

  /**
   * Clear all cache
   */
  clear() {
    this.cache.clear();
    this.cacheExpiry.clear();
  }

  /**
   * Clean up expired entries
   */
  cleanupExpired() {
    const now = Date.now();
    
    for (const [key, expiry] of this.cacheExpiry.entries()) {
      if (now > expiry) {
        this.delete(key);
      }
    }
  }

  /**
   * Get cache statistics
   */
  getStats() {
    return {
      size: this.cache.size,
      keys: Array.from(this.cache.keys())
    };
  }
}

// Create singleton instance
const cacheService = new CacheService();

/**
 * Higher-order function to add caching to API calls
 */
export const withCache = (apiFunction, cacheKey, ttl) => {
  return async (...args) => {
    const key = typeof cacheKey === 'function' ? cacheKey(...args) : cacheKey;
    
    // Try to get from cache first
    const cached = cacheService.get(key);
    if (cached) {
      return cached;
    }
    
    // Call API and cache result
    try {
      const result = await apiFunction(...args);
      cacheService.set(key, result, ttl);
      return result;
    } catch (error) {
      // Don't cache errors
      throw error;
    }
  };
};

/**
 * Cache keys for different API endpoints
 */
export const CACHE_KEYS = {
  SUBJECTS: 'subjects',
  USER_PROFILE: (userId) => `user_${userId}`,
  USER_SUBSCRIPTIONS: (userId) => `subscriptions_${userId}`,
  SUBJECT_STATUS: (userId, subject) => `status_${userId}_${subject}`,
  SURVEY: (userId, subject) => `survey_${userId}_${subject}`,
  LESSONS: (userId, subject) => `lessons_${userId}_${subject}`,
  LESSON_CONTENT: (userId, subject, lessonId) => `lesson_${userId}_${subject}_${lessonId}`
};

/**
 * Cache TTL configurations (in milliseconds)
 */
export const CACHE_TTL = {
  SHORT: 2 * 60 * 1000,      // 2 minutes
  MEDIUM: 5 * 60 * 1000,     // 5 minutes
  LONG: 15 * 60 * 1000,      // 15 minutes
  VERY_LONG: 60 * 60 * 1000  // 1 hour
};

export default cacheService;