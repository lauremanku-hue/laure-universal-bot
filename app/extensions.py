from flask_sqlalchemy import SQLAlchemy
from celery import Celery

# On définit l'objet ici, tout seul, au calme.
db = SQLAlchemy()
celery_app = Celery(__name__)


