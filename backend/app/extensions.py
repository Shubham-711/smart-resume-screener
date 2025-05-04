from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_marshmallow import Marshmallow
from celery import Celery

db = SQLAlchemy()
migrate = Migrate()
ma = Marshmallow()
# Celery instance created here, but configured inside create_app using Flask config
celery = Celery()