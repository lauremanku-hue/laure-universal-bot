import os
import sys

# Forçage immédiat du port
os.environ['PORT'] = '3000'

from app import create_app

app = create_app()

if __name__ == "__main__":
    # Démarrage direct sur 3000
    app.run(host="0.0.0.0", port=3000, debug=False)
