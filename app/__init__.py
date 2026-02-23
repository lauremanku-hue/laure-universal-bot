from flask import Flask
from .extensions import db
from .config import Config
from .celery_utils import make_celery

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    # 1. Initialisation de la DB
    db.init_app(app)

    # 2. INITIALISATION CELERY
    celery_instance = make_celery(app)
    app.extensions['celery'] = celery_instance 

    # 3. Enregistrement des routes (C'est ici que le 404 se joue !)
    from .routes import main as main_bp
    app.register_blueprint(main_bp)

    # 4. Préparation des tables
    with app.app_context():
        from . import models
        db.create_all()
        
        # DEBUG : On affiche toutes les routes enregistrées dans la console
        print("\n--- ROUTES ENREGISTRÉES ---")
        for rule in app.url_map.iter_rules():
            print(f"👉 {rule.endpoint}: {rule.rule} [{', '.join(rule.methods)}]")
        print("---------------------------\n")
    
    return app

