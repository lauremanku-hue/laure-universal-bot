web: gunicorn --bind 0.0.0.0:$PORT laure_bot:app
worker: celery -A celery_worker.celery worker --loglevel=info


