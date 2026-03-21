web: gunicorn --bind 0.0.0.0:3000 laure_web_launcher:app
worker: celery -A celery_worker.celery_app worker --loglevel=info
