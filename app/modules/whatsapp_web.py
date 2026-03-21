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
        self.client = NewClient("laure_session.db")
        self.ai = AIHandler()
        self.current_qr = None
        
    def on_qr(self, client, qr_string):
        self.current_qr = qr_string
        print("\n" + "="*50)
        print("🌟 NOUVEAU QR CODE GÉNÉRÉ 🌟")
        print("="*50 + "\n")
        
    def on_message(self, client, event: Message):
        # On ignore les messages envoyés par le bot lui-même
        if event.Info.IsFromMe:
            return

        # Récupération du message texte
        msg = event.Message.conversation or event.Message.extendedTextMessage.text
        if not msg:
            # On vérifie si c'est un message d'image avec légende
            if event.Message.imageMessage:
                msg = event.Message.imageMessage.caption
            elif event.Message.videoMessage:
                msg = event.Message.videoMessage.caption
        
        if not msg: return

        sender_jid = event.Info.Sender.String()
        # Nettoyage du JID pour la DB (on enlève le suffixe si c'est un utilisateur individuel)
        sender_id = sender_jid.split('@')[0] if "@s.whatsapp.net" in sender_jid else sender_jid
        
        is_group = "@g.us" in sender_jid
        
        print(f"📩 Message reçu de {sender_jid} ({'Groupe' if is_group else 'Privé'}) : {msg}")
        
        from flask import current_app
        app_to_use = getattr(self, 'app', None) or current_app
        
        with app_to_use.app_context():
            try:
                # 1. Récupération ou création de l'utilisateur
                user = User.query.filter_by(platform='whatsapp', platform_id=sender_id).first()
                if not user:
                    print(f"🆕 Nouvel utilisateur WhatsApp Web : {sender_id}")
                    user = User(platform='whatsapp', platform_id=sender_id, name="Utilisateur WA", bonus_given=True)
                    db.session.add(user)
                    db.session.commit()
                    
                    welcome_msg = (
                        "🌟 *BIENVENUE CHEZ LAURE !* 🌟\n\n"
                        "Merci de m'avoir contactée ! Tu as reçu un *bonus de 100 FCFA* pour tester mes services.\n\n"
                        "🎁 *OFFRE SPÉCIALE* : Je t'offre **3 JOURS d'accès VIP GRATUIT** ! 🎉\n"
                        "Profite des images IA, des téléchargements et des cours dès maintenant.\n\n"
                        "Tape *menu* pour voir tout ce que je peux faire pour toi !"
                    )
                    client.send_message(event.Info.Sender, welcome_msg)

                # 2. Logging du message
                new_log = MessageLog(
                    platform='whatsapp',
                    platform_id=sender_id,
                    message_id=event.Info.ID,
                    content=msg,
                    sender_name=event.Info.Pushname or "Inconnu"
                )
                db.session.add(new_log)
                db.session.commit()

                # 3. Traitement des réponses au Quiz
                clean_msg = msg.lower().strip()
                if clean_msg in ['a', 'b', 'c', 'd']:
                    session = QuizSession.query.filter_by(group_id=sender_id, status='active').first()
                    if session:
                        responses = json.loads(session.responses) if session.responses else {}
                        if sender_id not in responses: responses[sender_id] = []
                        responses[sender_id].append(clean_msg)
                        session.responses = json.dumps(responses)
                        db.session.commit()
                        return

                # 4. Traitement des commandes via le "cerveau" central (process_command)
                # On intercepte les commandes de téléchargement pour les gérer localement (Web mode)
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
                elif clean_msg.startswith("/img "):
                    if not user.is_premium:
                        client.reply_message("❌ *ACCÈS PREMIUM REQUIS*", event)
                        return
                    query = msg.split(' ', 1)[1]
                    client.reply_message("🎨 Je prépare ton image... Un instant !", event)
                    res = self.ai.generate_image_from_text(query)
                    if res['status'] == 'success':
                        client.send_image(event.Info.Sender, res['url'], caption=f"🎨 Voici ton image : {query}")
                    else:
                        client.reply_message(f"❌ Erreur image : {res.get('message')}", event)
                    return

                # Pour les autres commandes, on utilise process_command
                from app.routes import process_command
                resp = process_command(user, msg, 'whatsapp')
                if resp and 'message' in resp:
                    client.reply_message(resp['message'], event)

            except Exception as e:
                print(f"❌ Erreur on_message (Web): {e}")
                import traceback
                traceback.print_exc()

    def handle_download(self, client, event, query, is_audio):
        client.reply_message(f"📥 Recherche et téléchargement de '{query}' en cours...", event)
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
                client.reply_message(f"❌ Erreur lors de l'envoi du fichier : {e}", event)
        else:
            client.reply_message(f"❌ Erreur : {res.get('message')}", event)

    def start(self, app=None):
        self.app = app
        # Enregistrement du callback QR
        try:
            if hasattr(self.client, 'on_qr'):
                self.client.on_qr(self.on_qr)
            elif hasattr(self.client, 'qr_callback'):
                self.client.qr_callback(self.on_qr)
        except Exception as e:
            print(f"⚠️ Erreur lors de l'enregistrement du callback QR : {e}")

        # Note: QRCallback n'existe plus dans les versions récentes de neonize.
        # On utilise une méthode de détection dynamique pour enregistrer le gestionnaire de messages
        # car l'API de neonize peut varier selon la version installée.
        try:
            if hasattr(self.client, 'event_handler'):
                self.client.event_handler(Message)(self.on_message)
            elif hasattr(self.client, 'on_message'):
                self.client.on_message(self.on_message)
            else:
                # Fallback pour les versions qui utilisent un décorateur 'on'
                self.client.on(Message)(self.on_message)
            print("✅ Gestionnaire d'événements WhatsApp configuré.")
        except Exception as e:
            print(f"⚠️ Erreur lors de la configuration des événements : {e}")
            # Tentative ultime
            try:
                self.client.register_handler(Message, self.on_message)
            except:
                pass
        
        while True:
            try:
                print("🚀 Tentative de connexion WhatsApp Web...")
                self.client.connect()
                # Si connect() est bloquant et se termine, on attend un peu avant de relancer
                time.sleep(5)
            except Exception as e:
                print(f"❌ Erreur de connexion WhatsApp : {e}")
                time.sleep(10)

if __name__ == "__main__":
    bot = LaureWebBot()
    bot.start()
