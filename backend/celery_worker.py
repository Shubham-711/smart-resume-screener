import os
from app import create_app, celery # Import factory and celery instance

# Create a Flask app instance using the factory based on FLASK_ENV
# This ensures Celery tasks have access to the app context and config
config_name = os.getenv('FLASK_ENV') or 'default'
app = create_app(config_name=config_name)