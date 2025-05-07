# backend/app/__init__.py

import os
from flask import Flask
from flask_cors import CORS # <<< IMPORT CORS
from config import config_by_name # Import config dictionary from backend/config.py
# Import extension instances from app/extensions.py
from .extensions import db, ma, migrate, celery
import logging

# Configure basic logging for the app
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# --- Application Factory Function ---
def create_app(config_name=None):
    """Application Factory Pattern"""
    if config_name is None:
        config_name = os.getenv('FLASK_ENV', 'default')
    if config_name not in config_by_name:
         logger.warning(f"Config name '{config_name}' not found, falling back to 'default'.")
         config_name = 'default'

    app = Flask(__name__, instance_relative_config=True)
    app_config = config_by_name[config_name]
    app.config.from_object(app_config)
    # app.config.from_pyfile('config.py', silent=True) # Optional instance config

    logger.info(f"Creating Flask app with '{config_name}' configuration.")
    logger.debug(f"Database URI: {app.config.get('SQLALCHEMY_DATABASE_URI')}")
    logger.debug(f"Upload Folder: {app.config.get('UPLOAD_FOLDER')}")

    # --- Initialize CORS FIRST --- <<< INITIALIZE CORS HERE
    # Allow requests from the typical Vite React dev server origin
    # Make sure the port (e.g., 5173) matches where your frontend runs
    # In production, change origins to your deployed frontend URL
    CORS(app, resources={r"/api/*": {"origins": "http://localhost:5173"}}, supports_credentials=True)
    logger.info("Flask-CORS initialized, allowing requests from http://localhost:5173 for /api/* routes.")
    # ----------------------------

    # --- Initialize Flask Extensions AFTER CORS ---
    try:
        db.init_app(app)
        ma.init_app(app)
        migrate.init_app(app, db)
        logger.info("Database extensions initialized.")
    except Exception as e:
        logger.error(f"Error initializing database extensions: {e}", exc_info=True)

    # --- Configure Celery ---
    try:
        celery.conf.update(
            broker_url=app.config['CELERY_BROKER_URL'],
            result_backend=app.config['CELERY_RESULT_BACKEND'],
            task_ignore_result=True,
        )
        celery.conf.task_default_queue = 'default'
        class ContextTask(celery.Task):
            abstract = True
            def __call__(self, *args, **kwargs):
                with app.app_context():
                    return self.run(*args, **kwargs)
        celery.Task = ContextTask
        logger.info(f"Celery configured: Broker='{app.config['CELERY_BROKER_URL']}', Backend='{app.config['CELERY_RESULT_BACKEND']}'")
    except Exception as e:
        logger.error(f"Error configuring Celery: {e}", exc_info=True)

    # --- Create Upload Folder ---
    upload_folder = app.config.get('UPLOAD_FOLDER')
    if upload_folder:
        if not os.path.exists(upload_folder):
            try:
                os.makedirs(upload_folder)
                logger.info(f"Created configured upload folder: {upload_folder}")
            except OSError as e:
                logger.error(f"Error creating upload folder {upload_folder}: {e}", exc_info=True)
    else:
        logger.warning("UPLOAD_FOLDER not configured in Flask app config.")

    # --- Register Blueprints (API Routes) ---
    with app.app_context():
        try:
            from .routes.jobs import bp as jobs_bp
            from .routes.resumes import bp as resumes_bp
            app.register_blueprint(jobs_bp, url_prefix='/api/jobs')
            app.register_blueprint(resumes_bp, url_prefix='/api')
            logger.info("API Blueprints registered successfully.")
        except ImportError as e:
             logger.error(f"Failed to import or register blueprints: {e}", exc_info=True)
        except Exception as e:
             logger.error(f"Unexpected error during blueprint registration: {e}", exc_info=True)

    # --- Define Basic Routes (like Health Check) ---
    @app.route('/health')
    def health_check():
        """Simple health check endpoint."""
        return "OK", 200

    # --- Import Models ---
    from . import models
    logger.debug("Models imported.")

    # Return the configured Flask app instance
    return app