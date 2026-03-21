import os
import json
import time
from neonize.client import NewClient
from neonize.events import MessageEvent  # Changé : MessageEvent est plus stable
from .ai_handler import AIHandler
from .downloader import download_media

# Import Flask app and DB models
from flask import current_app
from app.extensions import db
from app.models import User, MessageLog, QuizSession

class LaureWebBot:
    def __init__(self):
        # Initialisation du client avec le fichier de session
        self.client = NewClient("laure_session.db")
        self.ai = AIHandler()
        self.current_qr = None
        self.pairing_code = None
        
    def on_qr(self, client, qr_string):
        self.current_qr = qr_string
        print("\n" + "="*50)
        print(f"🌟 SCANNE MOI POUR CONNECTER LAURE : {qr_string}")
        print("="*50 + "\n")

    def on_message(self, client, event: MessageEvent):
        # On ignore les messages envoyés par le bot lui-même
        if event.Info.IsFromMe:
            return

        # Récupération du message texte de manière sécurisée
        msg = ""
        if event.Message.conversation:
            msg = event.Message.conversation
        elif event.Message.extendedTextMessage and event.Message.extendedTextMessage.text:
            msg = event.Message.extendedTextMessage.text
        elif event.Message.imageMessage and event.Message.imageMessage.caption:
            msg = event.Message.imageMessage.caption
        elif event.Message.videoMessage and event.Message.videoMessage.caption:
            msg = event.Message.videoMessage.caption
        
        if not msg:
            return

        sender_jid = event.Info.Sender.String()
        # Nettoyage du JID pour la DB
        sender_id = sender_jid.split('@')
        
        is_group = "@g.us" in sender_jid
        
        print(f"📩 Message de {sender_id} : {msg}")
        
        # Utilisation sécurisée du contexte Flask
        app_to_use = getattr(self, 'app', None) or current_app
        
        with app_to_use.app_context():
            try:
                # 1. Gestion de l'utilisateur
                user = User.query.filter_by(platform='whatsapp', platform_id=sender_id).first()
                if not user:
                    user = User(platform='whatsapp', platform_id=sender_id, name="Étudiant", bonus_given=True)
                    db.session.add(user)
                    db.session.commit()
                    
                    welcome = "🌟 *BIENVENUE CHEZ LAURE !*\nTape *menu* pour commencer."
                    client.reply_message(welcome, event)

                # 2. Log du message
                new_log = MessageLog(
                    platform='whatsapp',
                    platform_id=sender_id,
                    content=msg,
                    sender_name=event.Info.Pushname or "Étudiant"
                )
                db.session.add(new_log)
                db.session.commit()

                # 3. Traitement des commandes IA / Images / Téléchargements
                clean_msg = msg.lower().strip()
                
                if clean_msg.startswith("/img "):
                    query = msg[5:]
                    client.reply_message("🎨 Je prépare ton image...", event)
                    res = self.ai.generate_image_from_text(query)
                    if res['status'] == 'success':
                        client.send_image(event.Info.Sender, res['url'], caption=f"🎨 Image : {query}")
                    return

                # 4. Traitement par le cerveau central (votre logique métier)
                from app.routes import process_command
                resp = process_command(user, msg, 'whatsapp')
                if resp and 'message' in resp:
                    client.reply_message(resp['message'], event)

            except Exception as e:
                print(f"❌ Erreur base de données : {e}")

    def start(self, app=None):
        self.app = app
        
        # CONFIGURATION DES HANDLERS (Version Neonize stable)
        # On utilise add_event_handler qui est la méthode recommandée
        print("⚙️ Configuration des écouteurs d'événements...")
        self.client.add_event_handler(MessageEvent, self.on_message)
        
        # Si vous voulez gérer le QR Code via console
        # Note: Sur Railway, il est préférable de se connecter une fois en local.
        
        while True:
            try:
                print("🚀 Connexion au serveur WhatsApp...")
                self.client.connect()
                # Cette ligne ne sera atteinte que si la connexion tombe
                time.sleep(5) 
            except Exception as e:
                print(f"⚠️ Déconnexion, tentative de reconnexion dans 10s : {e}")
                time.sleep(10)

if __name__ == "__main__":
    bot = LaureWebBot()
    bot.start()
