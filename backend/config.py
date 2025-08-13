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
    
    # JWT Configuration
    JWT_SECRET_KEY = os.environ.get('JWT_SECRET_KEY') or SECRET_KEY
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(hours=1)
    JWT_REFRESH_TOKEN_EXPIRES = timedelta(days=30)
    JWT_ALGORITHM = 'HS256'
    JWT_BLACKLIST_ENABLED = True
    JWT_BLACKLIST_TOKEN_CHECKS = ['access', 'refresh']
    
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
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'production-secret-key-must-be-set'
    
    # xAI API validation for production
    XAI_API_KEY = os.environ.get('XAI_API_KEY')
    
    # Production CORS settings
    CORS_ORIGINS = os.environ.get('CORS_ORIGINS', 'http://localhost:3000').split(',')
    
    @classmethod
    def validate_production_config(cls):
        """Validate production configuration at runtime"""
        if not os.environ.get('SECRET_KEY'):
            raise ValueError("SECRET_KEY environment variable must be set in production")
        if not os.environ.get('XAI_API_KEY'):
            raise ValueError("XAI_API_KEY environment variable must be set in production")
        if not os.environ.get('CORS_ORIGINS'):
            raise ValueError("CORS_ORIGINS environment variable must be set in production")
    
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