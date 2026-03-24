import os
import sys

# Utilisation du port fourni par Railway ou 3000 par défaut
port = int(os.environ.get('PORT', 3000))

from app import create_app

app = create_app()

if __name__ == "__main__":
    # Démarrage sur le port dynamique
    app.run(host="0.0.0.0", port=port, debug=False)
