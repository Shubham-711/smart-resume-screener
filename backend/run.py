import os
from app import create_app, db # Import factory and db instance
from app.models import Job, Resume # Import models for shell context

# Create the Flask app instance using the factory
# It will load config based on FLASK_ENV environment variable or default to DevelopmentConfig
config_name = os.getenv('FLASK_ENV') or 'default'
app = create_app(config_name=config_name)

# Make db and models available in 'flask shell' for easy testing/debugging
@app.shell_context_processor
def make_shell_context():
    """Provides application context for the Flask shell."""
    return {'db': db, 'Job': Job, 'Resume': Resume}

if __name__ == '__main__':
    # Get host and port from environment or use defaults
    # Host 0.0.0.0 makes it accessible on your network, not just localhost
    host = os.environ.get('FLASK_RUN_HOST', '0.0.0.0')
    try:
        port = int(os.environ.get('FLASK_RUN_PORT', '5000'))
    except ValueError:
        port = 5000

    # Debug mode is controlled by the config (e.g., DevelopmentConfig sets DEBUG=True)
    debug_mode = app.config.get('DEBUG', False)

    print(f"Starting Flask app in {config_name} mode...")
    app.run(host=host, port=port, debug=debug_mode)