"""
Configuration module for AI Recruiter Pro

This module contains configuration classes for different environments.
"""

import os
from datetime import timedelta


class DefaultConfig:
    """Base configuration with sensible defaults for all environments."""
    
    # Flask configuration
    SECRET_KEY = os.environ.get('SECRET_KEY', 'default-dev-key-change-in-production')
    DEBUG = False
    TESTING = False
    
    # SQLAlchemy configuration
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL', 'sqlite:///app.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_recycle': 300,
        'pool_pre_ping': True,
    }
    
    # JWT configuration
    JWT_SECRET_KEY = os.environ.get('JWT_SECRET_KEY', SECRET_KEY)
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(minutes=30)
    JWT_REFRESH_TOKEN_EXPIRES = timedelta(days=30)
    JWT_COOKIE_SECURE = False
    JWT_COOKIE_CSRF_PROTECT = True
    JWT_COOKIE_SAMESITE = "Lax"
    
    # File uploads
    UPLOAD_FOLDER = os.path.join(os.path.dirname(__file__), 'uploads')
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16 MB
    ALLOWED_EXTENSIONS = {'pdf', 'docx', 'doc', 'txt', 'rtf'}
    
    # OpenAI API
    OPENAI_API_KEY = os.environ.get('OPENAI_API_KEY')
    OPENAI_MODEL = 'gpt-4o'  # The newest OpenAI model is "gpt-4o"
    
    # Anthropic API
    ANTHROPIC_API_KEY = os.environ.get('ANTHROPIC_API_KEY')
    ANTHROPIC_MODEL = 'claude-3-5-sonnet-20241022'  # The newest Anthropic model is "claude-3-5-sonnet-20241022"
    
    # Feature flags
    FEATURE_FLAGS = {
        'use_openai': True,
        'use_anthropic': False,
        'enable_bulk_upload': True,
        'enable_job_tokens': True,
        'enable_api_v2': True,
        'enable_bias_detection': False,
    }


class DevelopmentConfig(DefaultConfig):
    """Development configuration."""
    
    DEBUG = True
    SQLALCHEMY_ECHO = True
    JWT_COOKIE_SECURE = False
    
    # For development, shorter token expiry
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(hours=1)
    
    # Override feature flags for development
    FEATURE_FLAGS = {
        **DefaultConfig.FEATURE_FLAGS,
        'enable_bias_detection': True,  # Enable in development for testing
    }


class TestingConfig(DefaultConfig):
    """Testing configuration."""
    
    TESTING = True
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    WTF_CSRF_ENABLED = False
    JWT_COOKIE_SECURE = False
    
    # Faster token expiry for testing
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(minutes=5)
    JWT_REFRESH_TOKEN_EXPIRES = timedelta(hours=1)
    
    # Use mock services in testing
    USE_MOCK_SERVICES = True


class ProductionConfig(DefaultConfig):
    """Production configuration."""
    
    # More secure settings for production
    JWT_COOKIE_SECURE = True
    JWT_COOKIE_SAMESITE = "Strict"
    
    # In production, override this with a strong secret key
    SECRET_KEY = os.environ.get('SECRET_KEY')
    JWT_SECRET_KEY = os.environ.get('JWT_SECRET_KEY', SECRET_KEY)
    
    # Higher connection pool limits for production
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_recycle': 300,
        'pool_pre_ping': True,
        'pool_size': 20,
        'max_overflow': 5,
    }
    
    # Production may want to disable certain features
    FEATURE_FLAGS = {
        **DefaultConfig.FEATURE_FLAGS,
        'enable_bulk_upload': os.environ.get('ENABLE_BULK_UPLOAD', 'true').lower() == 'true',
    }