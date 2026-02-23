import os

BASE_DIR = os.path.abspath(os.path.dirname(__file__))

class Config:
    # Sécurité
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'cle-secrete-dev-laure'
    
    # --- CONFIGURATION META / WHATSAPP ---
    # C'est ici que tu colles ton jeton temporaire et ton ID
    WHATSAPP_TOKEN = os.environ.get('WHATSAPP_TOKEN') or 'EAA5GmZBGK7bIBQySglj39CgtQRZB2ztAZBrtxRDI2QXVwzDZCYVV0yYYebjlH0cNXi89r8UPIKSdLZCfx3Nz6sWLx3BoNFR7gsG78ZC1siRaOeNl2Mw0DRTf3X1mSwbvAv2oDsE5Di0jnvCqYSlzehyLtzl6dfCF7V4zZBnpXFke4oQdV48ZA49VadDBDz7CQZBcHgJHtoDeTSXFbOuJbirkCpBZCgA7g84dyybQ2qz8cDQbeaUqBFvESswA6HhyXPpYay81oPWAnCCuOh6GSNW2qQy2aW'
    PHONE_NUMBER_ID = os.environ.get('PHONE_NUMBER_ID') or '1017539211438488'
    
    # Le code secret pour le Webhook (celui que tu as mis sur le site Meta)
    VERIFY_TOKEN = os.environ.get('VERIFY_TOKEN') or 'laure_secret'
    
    # --- TELEGRAM ---
    # Récupéré via @BotFather sur Telegram
    TELEGRAM_TOKEN = os.environ.get('TELEGRAM_TOKEN') or '8266533947:AAEz34KRYZEMSNbgL-0NaEKnQC0l7Ps-sfY'

    # --- FACEBOOK & INSTAGRAM ---
    # Pour Facebook/Instagram, on utilise souvent le même token Meta ou un Page Access Token
    FB_PAGE_ACCESS_TOKEN = os.environ.get('FB_PAGE_ACCESS_TOKEN') or 'TON_TOKEN_PAGE_FACEBOOK'

    # --- BASE DE DONNÉES (PostgreSQL) ---
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
        'postgresql://laure_user@127.0.0.1/laure_db'
    
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Optionnel : Pour éviter les erreurs de connexion perdue
    SQLALCHEMY_ENGINE_OPTIONS = {
        "pool_pre_ping": True,
    }

    # Configuration Celery / Redis
    CELERY_BROKER_URL = os.environ.get('REDIS_URL') or 'redis://localhost:6379/0'
    CELERY_RESULT_BACKEND = os.environ.get('REDIS_URL') or 'redis://localhost:6379/0' 

    # --- MODULE DOWNLOADER ---
    UPLOAD_FOLDER = os.path.join(BASE_DIR, 'downloads')

    if not os.path.exists(UPLOAD_FOLDER):
        os.makedirs(UPLOAD_FOLDER)
