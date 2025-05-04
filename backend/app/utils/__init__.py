import os
from flask import Flask
from config import config_by_name # Import config dictionary
from .extensions import db, ma, migrate, celery
import logging

# Configure basic logging for the app
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def create_app(config_name=None):
    """Application Factory Pattern"""
    if config_name is None:
        config_name = os.getenv('FLASK_ENV', 'default')

    if config_name not in config_by_name:
         logger.warning(f"Config name '{config_name}' not found, falling back to default.")
         config_name = 'default'

    app = Flask(__name__, instance_relative_config=True) # instance_relative_config=True allows loading instance/config.py
    app_config = config_by_name[config_name]
    app.config.from_object(app_config)

    # Load instance config if it exists (e.g., instance/config.py for secrets not in .env)
    # app.config.from_pyfile('config.py', silent=True)

    logger.info(f"Creating Flask app with '{config_name}' configuration.")

    # Initialize Flask extensions
    db.init_app(app)
    ma.init_app(app)
    migrate.init_app(app, db)

    # Configure Celery
    celery.conf.update(
        broker_url=app.config['CELERY_BROKER_URL'],
        result_backend=app.config['CELERY_RESULT_BACKEND'],
        task_ignore_result=True # Results often aren't needed directly
    )
    # Allow overriding other Celery settings via Flask config if needed
    # celery.conf.update(app.config.get('CELERY_SETTINGS', {}))
    celery.conf.task_default_queue = 'default' # Explicitly set a default queue

    # Subclass Celery Task to automatically push Flask app context for tasks
    class ContextTask(celery.Task):
        abstract = True
        def __call__(self, *args, **kwargs):
            # Ensure Flask app context is available within each task execution
            with app.app_context():
                return self.run(*args, **kwargs)

    celery.Task = ContextTask
    logger.info(f"Celery configured: Broker='{app.config['CELERY_BROKER_URL']}', Backend='{app.config['CELERY_RESULT_BACKEND']}'")


    # Create upload folder if it doesn't exist based on config
    upload_folder = app.config.get('UPLOAD_FOLDER')
    if upload_folder and not os.path.exists(upload_folder):
         try:
            os.makedirs(upload_folder)
            logger.info(f"Created upload folder: {upload_folder}")
         except OSError as e:
            logger.error(f"Error creating upload folder {upload_folder}: {e}", exc_info=True)

    # Register Blueprints (API endpoints)
    # Important: Import Blueprints *after* app and extensions are initialized
    try:
        from .routes.jobs import bp as jobs_bp
        app.register_blueprint(jobs_bp, url_prefix='/api/jobs')

        from .routes.resumes import bp as resumes_bp
        app.register_blueprint(resumes_bp, url_prefix='/api') # Routes defined within will refine path

        logger.info("API Blueprints registered.")
    except ImportError as e:
         logger.error(f"Failed to import or register blueprints: {e}", exc_info=True)


    # Simple health check route
    @app.route('/health')
    def health_check():
        # You could add checks here (e.g., db connection with try/except)
        return "OK", 200

    # Import models here to ensure they are known to SQLAlchemy/Migrate
    # Although they might be imported within routes/tasks as well
    from . import models

    return app