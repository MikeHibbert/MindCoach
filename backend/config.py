"""
Configuration settings for different environments
"""
import os
from datetime import timedelta

class Config:
    """Base configuration"""
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key-change-in-production'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max file size
    
    # xAI API Configuration
    XAI_API_KEY = os.environ.get('XAI_API_KEY')
    GROK_API_URL = os.environ.get('GROK_API_URL', 'https://api.x.ai/v1')
    
    # Cache settings
    CACHE_DEFAULT_TIMEOUT = 300  # 5 minutes
    CACHE_THRESHOLD = 1000
    
    # Performance settings
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_size': 10,
        'pool_recycle': 3600,
        'pool_pre_ping': True,
        'max_overflow': 20
    }
    
    # CORS settings
    CORS_ORIGINS = ['http://localhost:3000']
    
    # Logging
    LOG_LEVEL = 'INFO'
    LOG_MAX_BYTES = 10 * 1024 * 1024  # 10MB
    LOG_BACKUP_COUNT = 10

class DevelopmentConfig(Config):
    """Development configuration"""
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'sqlite:///learning_path_dev.db'
    
    # More verbose logging in development
    LOG_LEVEL = 'DEBUG'
    
    # Shorter cache timeouts for development
    CACHE_DEFAULT_TIMEOUT = 60

class ProductionConfig(Config):
    """Production configuration"""
    DEBUG = False
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'sqlite:///learning_path_prod.db'
    
    # Production security settings
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'fallback-secret-key'
    
    # xAI API validation for production
    XAI_API_KEY = os.environ.get('XAI_API_KEY')
    
    def __init__(self):
        super().__init__()
        # Only validate in production when this config is actually used
        if not os.environ.get('SECRET_KEY'):
            raise ValueError("SECRET_KEY environment variable must be set in production")
        if not self.XAI_API_KEY:
            raise ValueError("XAI_API_KEY environment variable must be set in production")
        cors_origins = os.environ.get('CORS_ORIGINS', '')
        if not cors_origins:
            raise ValueError("CORS_ORIGINS environment variable must be set in production")
    
    # Production CORS settings
    CORS_ORIGINS = os.environ.get('CORS_ORIGINS', 'http://localhost:3000').split(',')
    
    # Production performance settings
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_size': 20,
        'pool_recycle': 3600,
        'pool_pre_ping': True,
        'max_overflow': 40
    }
    
    # Longer cache timeouts in production
    CACHE_DEFAULT_TIMEOUT = 900  # 15 minutes

class TestingConfig(Config):
    """Testing configuration"""
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    WTF_CSRF_ENABLED = False
    
    # Disable caching in tests
    CACHE_DEFAULT_TIMEOUT = 0
    
    # Minimal logging in tests
    LOG_LEVEL = 'ERROR'

# Configuration mapping
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}