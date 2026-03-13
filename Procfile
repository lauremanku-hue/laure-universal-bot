web: gunicorn --bind 0.0.0.0:3000
worker: celery -A celery_worker.celery_app worker --loglevel=info
