import os
import json
import qrcode
import time
from neonize.client import NewClient
from neonize.events import Message
from .ai_handler import AIHandler
from .downloader import download_media

# Import Flask app and DB models
from flask import current_app
from app.extensions import db
from app.models import User, MessageLog, QuizSession

class LaureWebBot:
    def __init__(self):
        # Initialisation du client. On essaie de passer le callback QR directement si supporté.
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
        print("\n" + "="*50)
        print(f"🌟 NOUVEAU QR CODE : {qr_string}")
        print("="*50 + "\n")

    def pair_with_phone(self, phone_number):
        """Génère un code de couplage pour un numéro de téléphone"""
        try:
            phone = phone_number.replace("+", "").replace(" ", "").strip()
            print(f"📲 Demande de code de couplage pour : {phone}")
            
            if hasattr(self.client, 'PairPhone'):
                code = self.client.PairPhone(phone)
                self.pairing_code = code
                return code
            elif hasattr(self.client, 'pair_phone'):
                code = self.client.pair_phone(phone)
                self.pairing_code = code
                return code
            else:
                return "Méthode de couplage non supportée par cette version de neonize"
        except Exception as e:
            print(f"❌ Erreur lors du couplage par numéro : {e}")
            return str(e)
        
    def on_message(self, client, event: Message):
        if event.Info.IsFromMe:
            return

        # Récupération du message texte
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
        sender_id = sender_jid.split('@')[0] if "@s.whatsapp.net" in sender_jid else sender_jid
        is_group = "@g.us" in sender_jid
        
        print(f"📩 Message reçu de {sender_jid} : {msg}")
        
        # Gestion du contexte Flask
        app_to_use = self.app or current_app
        
        with app_to_use.app_context():
            try:
                user = User.query.filter_by(platform='whatsapp', platform_id=sender_id).first()
                if not user:
                    print(f"🆕 Nouvel utilisateur WhatsApp : {sender_id}")
                    user = User(platform='whatsapp', platform_id=sender_id, name="Utilisateur WA", bonus_given=True)
                    db.session.add(user)
                    db.session.commit()
                    
                    welcome_msg = (
                        "🌟 *BIENVENUE CHEZ LAURE !* 🌟\n\n"
                        "Merci de m'avoir contactée ! Tu as reçu un *bonus de 100 FCFA*.\n\n"
                        "🎁 *OFFRE* : 3 JOURS d'accès VIP GRATUIT ! 🎉\n"
                        "Tape *menu* pour voir mes services."
                    )
                    client.send_message(event.Info.Sender, welcome_msg)

                new_log = MessageLog(
                    platform='whatsapp',
                    platform_id=sender_id,
                    message_id=event.Info.ID,
                    content=msg,
                    sender_name=event.Info.Pushname or "Inconnu"
                )
                db.session.add(new_log)
                db.session.commit()

                clean_msg = msg.lower().strip()
                
                # Commandes spécifiques
                if clean_msg.startswith("/audio "):
                    if not user.is_premium:
                        client.reply_message("❌ *ACCÈS PREMIUM REQUIS*", event)
                        return
                    query = msg.split(' ', 1)[1]
                    self.handle_download(client, event, query, is_audio=True)
                    return
                
                elif clean_msg.startswith("/video "):
                    if not user.is_premium:
                        client.reply_message("❌ *ACCÈS PREMIUM REQUIS*", event)
                        return
                    query = msg.split(' ', 1)[1]
                    self.handle_download(client, event, query, is_audio=False)
                    return

                # Autres commandes
                from app.routes import process_command
                resp = process_command(user, msg, 'whatsapp')
                if resp and 'message' in resp:
                    client.reply_message(resp['message'], event)

            except Exception as e:
                print(f"❌ Erreur on_message : {e}")

    def handle_download(self, client, event, query, is_audio):
        client.reply_message(f"📥 Téléchargement de '{query}'...", event)
        res = download_media(query, is_audio=is_audio)
        if res['status'] == 'success':
            try:
                if is_audio:
                    client.send_audio(event.Info.Sender, res['file_path'])
                else:
                    client.send_video(event.Info.Sender, res['file_path'])
                
                if os.path.exists(res['file_path']):
                    os.remove(res['file_path'])
            except Exception as e:
                client.reply_message(f"❌ Erreur envoi : {e}", event)
        else:
            client.reply_message(f"❌ Erreur : {res.get('message')}", event)

    def start(self, app=None):
        self.app = app
        try:
            if hasattr(self.client, 'event_handler'):
                self.client.event_handler(Message)(self.on_message)
            else:
                self.client.on(Message)(self.on_message)
            print("✅ Gestionnaire WhatsApp configuré.")
        except Exception as e:
            print(f"⚠️ Erreur configuration événements : {e}")
        
        while True:
            try:
                print("🚀 Connexion WhatsApp Web...")
                self.client.connect()
                time.sleep(5)
            except Exception as e:
                print(f"❌ Erreur connexion : {e}")
                time.sleep(10)

if __name__ == "__main__":
    bot = LaureWebBot()
    bot.start()
