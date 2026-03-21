import os
from app import create_app

# Initialisation de l'application principale (Flask + Bot WhatsApp + Scheduler)
app = create_app()

if __name__ == "__main__":
    # Railway définit la variable PORT automatiquement (généralement 3000)
    port = int(os.environ.get("PORT", 3000))
    print(f"🌐 Serveur Laure Bot démarré sur le port {port}")
    
    # On lance l'application Flask
    # Le bot WhatsApp et le scheduler de cours sont lancés automatiquement par create_app()
    app.run(host='0.0.0.0', port=port, debug=False, use_reloader=False)
