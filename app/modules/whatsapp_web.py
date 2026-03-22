import os
import json
import time
import threading
from neonize.client import NewClient
from neonize.events import Message
from .ai_handler import AIHandler
from .downloader import download_media
from flask import current_app
from app.extensions import db
from app.models import User, MessageLog, QuizSession

class LaureWebBot:
    def __init__(self):
        try:
            self.client = NewClient("laure_session.db", qr_callback=self.on_qr)
        except:
            self.client = NewClient("laure_session.db")
        
        self.ai = AIHandler()
        self.current_qr = None
        self.pairing_code = None
        self.app = None

    def on_qr(self, client, qr_string):
        self.current_qr = qr_string
        print(f"\n🌟 QR CODE WHATSAPP : {qr_string}\n")

    def on_message(self, client, event: Message):
        if event.Info.IsFromMe:
            return

        # Extraction du texte
        msg = event.Message.conversation or ""
        if not msg and event.Message.extendedTextMessage:
            msg = event.Message.extendedTextMessage.text
        if not msg and event.Message.imageMessage:
            msg = event.Message.imageMessage.caption
            
        if not msg: return

        sender_jid = event.Info.Sender.String()
        sender_id = sender_jid.split('@')[0]
        
        # Utilisation du contexte Flask
        with self.app.app_context():
            try:
                user = User.query.filter_by(platform='whatsapp', platform_id=sender_id).first()
                if not user:
                    user = User(platform='whatsapp', platform_id=sender_id, name=event.Info.Pushname or "Utilisateur WA")
                    db.session.add(user)
                    db.session.commit()
                    client.send_message(event.Info.Sender, "🌟 *Bienvenue chez Laure !* Tape *menu* pour commencer.")

                # Log
                log = MessageLog(platform='whatsapp', platform_id=sender_id, content=msg)
                db.session.add(log)
                db.session.commit()

                clean_msg = msg.lower().strip()

                # Commandes prioritaires
                if clean_msg.startswith(("/audio ", "/video ")):
                    if not user.is_premium:
                        client.reply_message("❌ Accès Premium requis.", event)
                        return
                    is_audio = "/audio" in clean_msg
                    query = msg.split(' ', 1)[1]
                    self.handle_download(client, event, query, is_audio)
                    return

                # Logique standard via routes.py
                from app.routes import process_command
                resp = process_command(user, msg, 'whatsapp')
                if resp and 'message' in resp:
                    client.reply_message(resp['message'], event)
                else:
                    ai_res = self.ai.chat(msg)
                    client.reply_message(ai_res, event)

            except Exception as e:
                print(f"❌ Erreur DB: {e}")

    def handle_download(self, client, event, query, is_audio):
        client.reply_message(f"📥 Téléchargement de {query}...", event)
        res = download_media(query, is_audio)
        if res['status'] == 'success':
            try:
                if is_audio:
                    client.send_audio(event.Info.Sender, res['file_path'])
                else:
                    client.send_video(event.Info.Sender, res['file_path'])
                if os.path.exists(res['file_path']): os.remove(res['file_path'])
            except Exception as e:
                client.reply_message(f"❌ Erreur envoi: {e}", event)
        else:
            client.reply_message(f"❌ {res.get('message')}", event)

    def start(self, app):
        self.app = app
        try:
            # Enregistrement dynamique du handler selon la version de neonize
            if hasattr(self.client, 'event_handler'):
                self.client.event_handler(Message)(self.on_message)
            else:
                self.client.on(Message)(self.on_message)
            
            print("🚀 Bot WhatsApp en cours de connexion...")
            self.client.connect()
        except Exception as e:
            print(f"⚠️ Erreur démarrage Bot: {e}")
