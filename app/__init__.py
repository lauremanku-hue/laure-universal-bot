import os
from flask import Flask
from .extensions import db, celery_app
from .routes import main

def create_app():
    import os
    app = Flask(__name__)
    
    # Configuration
    # On utilise DATABASE_URL de Railway, sinon un sqlite local
    database_url = os.environ.get('DATABASE_URL')
    if database_url and database_url.startswith("postgres://"):
        database_url = database_url.replace("postgres://", "postgresql://", 1)
    
    app.config['SQLALCHEMY_DATABASE_URI'] = database_url or 'sqlite:///laure_bot.db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    # Initialisation des extensions
    db.init_app(app)
    
    # Configuration Celery
    celery_app.conf.update(
        broker_url=os.environ.get('REDIS_URL', 'redis://localhost:6379/0'),
        result_backend=os.environ.get('REDIS_URL', 'redis://localhost:6379/0'),
        task_ignore_result=True
    )
    
    # On attache celery à l'app pour y accéder facilement
    if not hasattr(app, 'extensions'):
        app.extensions = {}
    app.extensions['celery'] = celery_app
    
    # Enregistrement des blueprints
    app.register_blueprint(main)
    
    return app

