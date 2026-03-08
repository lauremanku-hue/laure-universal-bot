from app import create_app

# Initialisation de l'application Flask
app = create_app()

# Extraction sécurisée de Celery pour le worker Linux
# On utilise .get() pour éviter le crash et on affiche un message clair
celery_app = app.extensions.get('celery')

if celery_app is None:
    print("❌ ERREUR FATALE : L'instance Celery n'a pas pu être chargée.")
else:
    print("🚀 Worker Celery prêt à recevoir des tâches.")

