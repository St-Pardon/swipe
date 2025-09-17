"""Configuration package for the Swipe application."""

import os
from datetime import timedelta

class Config:
    """Base configuration class."""
    
    # Basic Flask configuration
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key-change-in-production'
    
    # Database configuration
    def _normalize_db_url(url: str) -> str:
        """Normalize DATABASE_URL for SQLAlchemy.
        - Map deprecated "postgres://" to "postgresql://"
        - Prefer psycopg3 by forcing dialect "postgresql+psycopg://" when no driver specified
        """
        if not url:
            return 'sqlite:///swipe.db'
        # Replace deprecated scheme
        if url.startswith('postgres://'):
            url = 'postgresql://' + url[len('postgres://'):]
        # If postgresql URL without explicit driver, force psycopg3
        if url.startswith('postgresql://') and '+psycopg' not in url and '+psycopg2' not in url:
            url = 'postgresql+psycopg://' + url[len('postgresql://'):]
        return url

    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'sqlite:///swipe.db'

    # SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'sqlite:///swipe.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # JWT configuration
    JWT_SECRET_KEY = os.environ.get('JWT_SECRET_KEY') or SECRET_KEY
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(hours=1)
    JWT_REFRESH_TOKEN_EXPIRES = timedelta(days=30)
    
    # Mail configuration
    MAIL_SERVER = os.environ.get('MAIL_SERVER')
    MAIL_PORT = int(os.environ.get('MAIL_PORT') or 587)
    MAIL_USE_TLS = os.environ.get('MAIL_USE_TLS', 'true').lower() in ['true', 'on', '1']
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME')
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD')
    
    # Application settings
    ITEMS_PER_PAGE = 20
    
    # Encryption settings
    ACCOUNT_ENCRYPTION_KEY = os.environ.get('ACCOUNT_ENCRYPTION_KEY') or 'dev-encryption-key-change-in-production'
    
class DevelopmentConfig(Config):
    """Development configuration."""
    DEBUG = True
    
class ProductionConfig(Config):
    """Production configuration."""
    DEBUG = False
    
class TestingConfig(Config):
    """Testing configuration."""
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'

# Configuration dictionary
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}
