import os
from flask import Flask
from .extensions import db, celery_app
from .routes import main

def create_app():
    import os
    from flask import send_from_directory
    app = Flask(__name__, static_folder='../dist', static_url_path='/')
    
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
    from .routes import main, bot
    app.register_blueprint(main)
    
    # Démarrage du bot WhatsApp Web en arrière-plan (Thread séparé pour ne pas bloquer Gunicorn)
    import threading
    bot_thread = threading.Thread(target=bot.start, args=(app,))
    bot_thread.daemon = True
    bot_thread.start()
    print("🤖 Bot WhatsApp Web démarré en tâche de fond.")
    
    # Configuration Webhook Telegram (si Token et APP_URL présents)
    from .routes import tg
    app_url = os.environ.get('APP_URL')
    if tg and app_url:
        tg.set_webhook(app_url)
        tg.set_bot_commands()

    # Création automatique des tables au démarrage
    with app.app_context():
        db.create_all()
        print("🗄️ Base de données initialisée (Tables créées).")

    # Thread de fond pour les cours programmés
    def start_course_scheduler(app):
        from .tasks import send_scheduled_courses
        with app.app_context():
            while True:
                try:
                    send_scheduled_courses()
                except Exception as e:
                    print(f"⚠️ Erreur Scheduler Cours : {e}")
                import time
                time.sleep(60) # Vérifier chaque minute

    import threading
    scheduler_thread = threading.Thread(target=start_course_scheduler, args=(app,))
    scheduler_thread.daemon = True
    scheduler_thread.start()
    print("⏰ Scheduler de cours démarré.")
    
    return app
