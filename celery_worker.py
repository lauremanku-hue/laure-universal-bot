from app import create_app

app = create_app()
celery = app.extensions.get('celery')

# Extraction sécurisée de Celery pour le worker Linux
# On utilise .get() pour éviter le crash et on affiche un message clair
celery = app.extensions.get('celery')

if celery is None:
    print("❌ ERREUR FATALE : L'instance Celery n'a pas pu être chargée.")
else:
    print("🚀 Worker Celery prêt à recevoir des tâches.")

