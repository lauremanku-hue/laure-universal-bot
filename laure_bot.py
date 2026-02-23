import os
import sys
import shutil

def clean_cache():
    """Supprime les fichiers compilés qui peuvent causer des erreurs."""
    for root, dirs, files in os.walk('.', topdown=False):
        for name in dirs:
            if name == "__pycache__":
                shutil.rmtree(os.path.join(root, name))

# Ajout du dossier actuel au PATH pour les imports
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

def start_server():
    print("\n" + "═"*50)
    print(" 🛠️  SYSTÈME DE DIAGNOSTIC LAURE-UNIVERSEL")
    print("═"*50)
    
    try:
        from app import create_app, db
        app = create_app()
        
        with app.app_context():
            # Synchronisation de la base de données
            db.create_all()
            print("✅ Base de données : Synchronisée")

        port = 5000
        print(f"🚀 Serveur Flask : Actif sur http://0.0.0.0:{port}")
        print("💡 Appuyez sur CTRL+C pour arrêter.")
        print("═"*50 + "\n")
        
        app.run(host='0.0.0.0', port=port, debug=True)
        
    except Exception as e:
        print(f"💥 ERREUR FATALE AU DÉMARRAGE : {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    clean_cache()
    start_server()

