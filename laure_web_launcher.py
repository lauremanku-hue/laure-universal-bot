
import os
import sys
import time
import threading
import qrcode
import io
from flask import Flask, send_file, Response, render_template_string
from app import create_app
from app.modules.whatsapp_web import LaureWebBot

# On initialise l'application principale (avec toutes les routes : Monetbil, Telegram, etc.)
app = create_app()
bot = LaureWebBot()

# On ajoute les routes spécifiques au QR code à l'application principale
@app.route('/qr-status')
def qr_status():
    return f"<h1>QR Status</h1><p>{'Prêt' if bot.current_qr else 'En attente...'}</p><img src='/qr-code-image' />"

@app.route('/qr-code-image')
def qr_code_image():
    if not bot.current_qr:
        return "Pas de QR code disponible", 404
    img = qrcode.make(bot.current_qr)
    buf = io.BytesIO()
    img.save(buf, format='PNG')
    buf.seek(0)
    return send_file(buf, mimetype='image/png')

def run_bot():
    print("🚀 Démarrage du bot WhatsApp (Thread)...")
    try:
        bot.start()
    except Exception as e:
        print(f"❌ Erreur critique du bot : {e}")

if __name__ == "__main__":
    # Lancement du bot dans un thread séparé
    bot_thread = threading.Thread(target=run_bot, daemon=True)
    bot_thread.start()
    
    # Lancement du serveur Flask sur le port 5000 (proxy par Vite sur 3000)
    # En production, le port sera 3000
    port = int(os.environ.get("PORT", 5000))
    print(f"🌐 Serveur Web (Full Stack) démarré sur le port {port}")
    app.run(host='0.0.0.0', port=port, debug=False, use_reloader=False)
