import os
import sys

# Sécurité : On force l'ajout du dossier actuel au chemin de recherche Python
# Cela permet de trouver le dossier 'app' sans erreur
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import create_app

# On initialise l'application
app = create_app()

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 3000))
    
    print("\n" + "="*50)
    print("🌟 LAURE-UNIVERSEL : DÉMARRAGE DU MOTEUR 🌟")
    print(f"📡 Serveur actif sur : http://0.0.0.0:{port}")
    print("="*50 + "\n")
    
    app.run(host='0.0.0.0', port=port, debug=True)

