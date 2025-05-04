# backend/app/__init__.py

import os
from flask import Flask
from config import config_by_name # Import config dictionary from backend/config.py
# Import extension instances from app/extensions.py
from .extensions import db, ma, migrate, celery
import logging

# Configure basic logging for the app
# This will log to console by default when running flask run
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
# Get a logger specific to this module
logger = logging.getLogger(__name__)

def create_app(config_name=None):
    """
    Application Factory Pattern:
    Creates and configures the Flask application instance.
    Args:
        config_name (str, optional): The name of the configuration to use
                                     (e.g., 'development', 'production').
                                     Defaults to FLASK_ENV or 'default'.
    Returns:
        Flask: The configured Flask application instance.
    """
    if config_name is None:
        # Get configuration name from environment variable or use default
        config_name = os.getenv('FLASK_ENV', 'default')

    # Handle case where provided config_name isn't valid
    if config_name not in config_by_name:
         logger.warning(f"Config name '{config_name}' not found in config.py, falling back to 'default'.")
         config_name = 'default'

    # Create the Flask application instance
    # instance_relative_config=True allows loading config from an 'instance' folder (optional)
    app = Flask(__name__, instance_relative_config=True)

    # Load configuration from the selected class in config.py
    app_config = config_by_name[config_name]
    app.config.from_object(app_config)

    # Optional: Load instance config if it exists (e.g., instance/config.py for secrets)
    # This allows overriding config values without modifying versioned files
    # app.config.from_pyfile('config.py', silent=True)

    logger.info(f"Creating Flask app with '{config_name}' configuration.")
    logger.debug(f"Database URI: {app.config.get('SQLALCHEMY_DATABASE_URI')}") # Log DB URI for debugging (might show password!)
    logger.debug(f"Upload Folder: {app.config.get('UPLOAD_FOLDER')}")

    # --- Initialize Flask Extensions ---
    try:
        db.init_app(app)        # Initialize SQLAlchemy with the app
        ma.init_app(app)        # Initialize Marshmallow with the app
        migrate.init_app(app, db) # Initialize Flask-Migrate
        logger.info("Database extensions (SQLAlchemy, Migrate, Marshmallow) initialized.")
    except Exception as e:
        logger.error(f"Error initializing database extensions: {e}", exc_info=True)
        # Depending on severity, you might want to raise the error or exit

    # --- Configure Celery ---
    try:
        # Update the Celery instance's configuration using settings from the Flask app config
        celery.conf.update(
            broker_url=app.config['CELERY_BROKER_URL'],
            result_backend=app.config['CELERY_RESULT_BACKEND'],
            task_ignore_result=True, # Often results aren't needed directly via backend, saves storage
            # Optional: Add other Celery config items here or load from app.config dict
            # timezone = 'UTC',
            # enable_utc = True,
        )
        celery.conf.task_default_queue = 'default' # Explicitly set a default queue name

        # Subclass Celery Task to automatically add Flask app context to tasks
        # This makes db, current_app, etc. available inside Celery tasks
        class ContextTask(celery.Task):
            abstract = True # Mark as abstract so it's not registered as a task itself
            def __call__(self, *args, **kwargs):
                # Ensure Flask app context is available within each task execution
                with app.app_context():
                    return self.run(*args, **kwargs)

        celery.Task = ContextTask # Set the custom Task class as the default for Celery
        logger.info(f"Celery configured: Broker='{app.config['CELERY_BROKER_URL']}', Backend='{app.config['CELERY_RESULT_BACKEND']}'")
    except Exception as e:
        logger.error(f"Error configuring Celery: {e}", exc_info=True)


    # --- Create Upload Folder ---
    # Ensure the folder configured for uploads exists
    upload_folder = app.config.get('UPLOAD_FOLDER')
    if upload_folder:
        if not os.path.exists(upload_folder):
            try:
                os.makedirs(upload_folder)
                logger.info(f"Created configured upload folder: {upload_folder}")
            except OSError as e:
                logger.error(f"Error creating upload folder {upload_folder}: {e}", exc_info=True)
                # Consider if this should be a fatal error preventing app start
    else:
        logger.warning("UPLOAD_FOLDER not configured in Flask app config.")


    # --- Register Blueprints (API Routes) ---
    # Important: Import Blueprints *after* app and extensions are initialized to avoid circular imports
    with app.app_context(): # Ensure context for blueprint registration if needed
        try:
            # Import the blueprint objects defined in the routes files
            from .routes.jobs import bp as jobs_bp
            from .routes.resumes import bp as resumes_bp

            # Register the blueprints with the Flask app, setting URL prefixes
            app.register_blueprint(jobs_bp, url_prefix='/api/jobs')
            app.register_blueprint(resumes_bp, url_prefix='/api') # Routes within will refine paths like /jobs/<id>/resumes

            logger.info("API Blueprints registered successfully.")
        except ImportError as e:
             logger.error(f"Failed to import or register blueprints: {e}", exc_info=True)
             # This is likely a fatal error for the app's functionality
        except Exception as e:
             logger.error(f"Unexpected error during blueprint registration: {e}", exc_info=True)


    # --- Define Basic Routes (like Health Check) ---
    @app.route('/health')
    def health_check():
        """Simple health check endpoint."""
        # You could add checks here (e.g., db connection with try/except)
        return "OK", 200

    # --- Import Models ---
    # Ensure models are imported so SQLAlchemy/Flask-Migrate knows about them.
    # Importing here is generally safe after extensions are initialized.
    from . import models
    logger.debug("Models imported.")

    # Return the configured Flask app instance
    return app