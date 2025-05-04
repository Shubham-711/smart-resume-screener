import os
from dotenv import load_dotenv

# Load environment variables from .env file located in the same directory (backend/)
basedir = os.path.abspath(os.path.dirname(__file__))
load_dotenv(os.path.join(basedir, '.env'))

class Config:
    """Base configuration."""
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'a-default-secret-key-change-it' # CHANGE THIS IN .ENV
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
        'sqlite:///' + os.path.join(basedir, 'instance/app.db') # Default to SQLite in instance folder if no DB_URL
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    DEBUG = False

    # Celery Configuration (loaded from .env)
    CELERY_BROKER_URL = os.environ.get('CELERY_BROKER_URL') or 'redis://localhost:6379/0'
    CELERY_RESULT_BACKEND = os.environ.get('CELERY_RESULT_BACKEND') or 'redis://localhost:6379/1'

    # File Upload Configuration (loaded from .env)
    UPLOAD_FOLDER = os.environ.get('UPLOAD_FOLDER') or os.path.join(basedir, 'uploads/resumes')
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024 # 16 MB limit for uploads
    ALLOWED_EXTENSIONS = {'pdf', 'docx'}

class DevelopmentConfig(Config):
    """Development configuration."""
    DEBUG = True
    # SQLALCHEMY_ECHO = True # Uncomment to see SQL queries printed

class ProductionConfig(Config):
    """Production configuration."""
    # Ensure SECRET_KEY and DATABASE_URL are securely set via environment variables
    pass # Add any other production-specific overrides

class TestingConfig(Config):
    """Testing configuration."""
    TESTING = True
    SQLALCHEMY_DATABASE_URI = os.environ.get('TEST_DATABASE_URL') or \
        'sqlite:///' + os.path.join(basedir, 'instance/test.db') # Use a separate test DB
    CELERY_ALWAYS_EAGER = True # Run tasks synchronously for testing
    WTF_CSRF_ENABLED = False # Often disabled for testing APIs

# Dictionary to map environment names to config classes
config_by_name = dict(
    development=DevelopmentConfig,
    production=ProductionConfig,
    testing=TestingConfig,
    default=DevelopmentConfig
)

def get_config_name():
    # Get config name from FLASK_ENV, default to 'default' -> DevelopmentConfig
    return os.getenv('FLASK_ENV', 'default')

def get_config():
    config_name = get_config_name()
    return config_by_name.get(config_name, DevelopmentConfig)

# Instantiate the config object for potential direct import (though using factory is preferred)
# config = get_config()