from app import create_app
import os

# Création de l'objet app pour Gunicorn
app = create_app()

if __name__ == "__main__":
    # Forçage du port 3000 pour le démarrage manuel
    port = int(os.environ.get("PORT", 3000))
    app.run(host="0.0.0.0", port=port)
