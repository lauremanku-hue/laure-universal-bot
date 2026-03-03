# Laure Universel - Backend Bot

Ce projet est le moteur du bot Laure, capable de gérer WhatsApp, Telegram, Messenger et Instagram.

## Arborescence du Projet

```text
laure_universel/
├── app/                    # Code principal de l'application Flask
│   ├── modules/            # Handlers spécifiques par plateforme et IA
│   │   ├── ai_handler.py       # Moteur Gemini / IA
│   │   ├── meta_handler.py     # Messenger & Instagram
│   │   ├── telegram_handler.py # Telegram
│   │   ├── whatsapp_handler.py # WhatsApp
│   │   └── downloader.py       # Téléchargement YouTube/FB/IG
│   ├── models.py           # Modèles de base de données (Users, Courses)
│   ├── routes.py           # Webhooks et logique des commandes
│   ├── tasks.py            # Tâches asynchrones (Celery)
│   └── __init__.py         # Initialisation de l'app Flask
├── celery_worker.py        # Point d'entrée pour le worker Celery
├── laure_bot.py            # Script de lancement principal
├── requirements.txt        # Dépendances Python
└── .env                    # Variables secrètes (NE PAS ENVOYER SUR GIT)
```

## Installation

1. Créer un environnement virtuel : `python -m venv venv`
2. L'activer : `source venv/bin/activate` (Linux/Mac) ou `venv\Scripts\activate` (Windows)
3. Installer les dépendances : `pip install -r requirements.txt`
4. Configurer le fichier `.env`
5. Lancer le bot (développement) : `python laure_bot.py`
6. Lancer le bot (production) : `gunicorn laure_bot:app`
