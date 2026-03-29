
from apscheduler.schedulers.background import BackgroundScheduler
from datetime import datetime, timedelta
import os
import json
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
        try:
            self.client = NewClient("laure_session.db")
        except:
            self.client = NewClient("laure_session.db") 

        self.ai = AIHandler()
        self.pairing_code = None
        self.scheduler = BackgroundScheduler()
        self.scheduler.add_job(self.send_reminders, 'interval', hours=12)
        self.scheduler.add_job(self.send_scheduled_courses, 'interval', minutes=1)
        self.scheduler.start()
        
    def send_scheduled_courses(self):
        """Envoie les cours programmés à l'heure prévue."""
        if not hasattr(self, 'app'): return
        with self.app.app_context():
            now = datetime.utcnow()
            current_time = now.strftime("%H:%M")
            current_day = now.weekday()
            
            from app.models import ScheduledCourse
            courses = ScheduledCourse.query.filter_by(
                day_of_week=current_day, 
                scheduled_time=current_time, 
                is_active=True
            ).all()
            
            for course in courses:
                content = self.ai.generate_course_content(course.title)
                self.client.send_message(course.target_jid, f"📚 *COURS DU JOUR : {course.title.upper()}*\n\n{content}")
        
    def send_reminders(self):
        """Envoie des rappels aux utilisateurs inactifs ou ayant un quiz en cours."""
        if not hasattr(self, 'app'): return
        
        with self.app.app_context():
            # Rappel pour les quiz inachevés
            yesterday = datetime.utcnow() - timedelta(days=1)
            active_sessions = QuizSession.query.filter(QuizSession.status == 'active', QuizSession.created_at < yesterday).all()
            
            for session in active_sessions:
                try:
                    msg = "👋 Salut ! Tu n'as pas fini ton quiz d'hier. On s'y remet ? Tape *quiz* pour continuer !"
                    # On envoie au groupe ou à l'utilisateur
                    jid = f"{session.group_id}@s.whatsapp.net" if "@" not in session.group_id else session.group_id
                    self.client.send_message(jid, msg)
                    # On marque comme rappelé pour ne pas spammer (on pourrait ajouter un champ 'reminded')
                except:
                    pass

    def get_pairing_code(self, phone_number):
        """Génère un code de couplage pour un numéro de téléphone."""
        try:
            phone = "".join(filter(str.isdigit, phone_number))
            print(f"📲 Tentative de couplage pour : {phone}")

            # 1. Vérification de la connexion (Gestion bool vs function)
            connected = self.client.is_connected
            if callable(connected):
                connected = connected()
            
            if connected:
                return {"status": "error", "message": "Déjà connecté !"}

            # 2. Tentative de couplage
            # On cherche la méthode (pair_with_phone ou PairWithPhone)
            method_name = None
            if hasattr(self.client, "pair_with_phone"):
                method_name = "pair_with_phone"
            elif hasattr(self.client, "PairWithPhone"):
                method_name = "PairWithPhone"

            if method_name:
                method = getattr(self.client, method_name)
                # Si c'est une méthode, on l'appelle, sinon on prend la valeur
                code = method(phone) if callable(method) else method
                
                self.pairing_code = code
                return {"status": "success", "code": code}
            
            return {"status": "error", "message": "Méthode de couplage introuvable sur ce client."}

        except Exception as e:
            print(f"❌ Erreur critique pairing : {e}")
            return {"status": "error", "message": f"Erreur technique : {e}"}

    def on_message(self, client, event: Message):
        if event.Info.IsFromMe: return

        # Récupération du texte et de l'image éventuelle
        msg = event.Message.conversation or event.Message.extendedTextMessage.text
        image_path = None
        
        if event.Message.imageMessage:
            msg = event.Message.imageMessage.caption or ""
            # Téléchargement de l'image
            try:
                if not os.path.exists('downloads'): os.makedirs('downloads')
                image_path = f"downloads/img_{event.Info.ID}.jpg"
                data = client.download_any(event.Message.imageMessage)
                with open(image_path, "wb") as f:
                    f.write(data)
            except Exception as e:
                print(f"❌ Erreur téléchargement image : {e}")

        if not msg and not image_path: return

        sender_jid = event.Info.Sender.String()
        sender_id = sender_jid.split('@')[0] if "@s.whatsapp.net" in sender_jid else sender_jid
        
        app_to_use = getattr(self, 'app', None) or current_app
        with app_to_use.app_context():
            try:
                user = User.query.filter_by(platform='whatsapp', platform_id=sender_id).first()
                if not user:
                    user = User(platform='whatsapp', platform_id=sender_id, name=event.Info.Pushname or "Utilisateur")
                    db.session.add(user)
                    db.session.commit()
                    client.reply_message(
                        "🌟 *BIENVENUE CHEZ LAURE !* 🌟\n\n"
                        "Je suis ton assistante IA. Tu as *3 JOURS D'ESSAI GRATUIT* pour tester toutes mes fonctionnalités !\n\n"
                        "Après ces 3 jours, tu devras passer au mode *VIP* pour continuer à m'utiliser.\n\n"
                        "Tape *menu* pour découvrir mes services.", event
                    )

                user.last_active = datetime.utcnow()
                db.session.commit()

                # Vérification de l'accès (Essai ou Premium)
                if not user.has_access():
                    client.reply_message(
                        "❌ *TON ESSAI A EXPIRÉ*\n\n"
                        "Tes 3 jours d'essai gratuit sont terminés. Pour continuer à utiliser Laure, tu dois t'abonner au mode VIP.\n\n"
                        "Tape *vip* pour voir les offres et *payer* pour t'abonner.", event
                    )
                    return

                clean_msg = msg.lower().strip() if msg else ""

                # Gestion des Quiz en cours
                session = QuizSession.query.filter_by(group_id=sender_id, status='active').first()
                if session and clean_msg in ['a', 'b', 'c', 'd']:
                    questions = json.loads(session.questions_data)
                    current_q = questions[session.current_question_index]
                    
                    # Vérification de la réponse
                    is_correct = clean_msg.upper() == current_q['correct'].upper()
                    if is_correct:
                        session.correct_answers_count += 1
                    
                    session.current_question_index += 1
                    
                    if session.current_question_index >= session.total_questions:
                        # Fin du quiz - Stats
                        session.status = 'completed'
                        pct = (session.correct_answers_count / session.total_questions) * 100
                        report = (
                            f"🏁 *QUIZ TERMINÉ !*\n\n"
                            f"📊 *STATS* :\n"
                            f"- Total : {session.total_questions}\n"
                            f"- Justes : {session.correct_answers_count}\n"
                            f"- Fausses : {session.total_questions - session.correct_answers_count}\n"
                            f"- Score : {pct:.1f}%\n\n"
                            f"💡 *CORRECTION* : Révise les points où tu as hésité !"
                        )
                        client.reply_message(report, event)
                    else:
                        # Question suivante
                        next_q = questions[session.current_question_index]
                        client.reply_message(
                            f"📚 *QUESTION {session.current_question_index + 1}/{session.total_questions}*\n\n"
                            f"{next_q['q']}\n\n"
                            f"A) {next_q['a']}\n"
                            f"B) {next_q['b']}\n"
                            f"C) {next_q['c']}\n"
                            f"D) {next_q['d']}", event
                        )
                    db.session.commit()
                    return

                # Commandes spécifiques
                if clean_msg == 'prof':
                    user.mode = 'professeur' if user.mode == 'normal' else 'normal'
                    db.session.commit()
                    status = "🎓 *MODE PROFESSEUR ACTIVÉ*" if user.mode == 'professeur' else "🏠 *MODE NORMAL RÉACTIVÉ*"
                    client.reply_message(status, event)
                    return

                # Gestion des téléchargements (Gratuit pendant l'essai ou pour les VIP)
                if clean_msg.startswith("/audio "):
                    query = msg.split(' ', 1)[1]
                    self.handle_download(client, event, query, is_audio=True)
                    return

                if clean_msg.startswith("/video "):
                    query = msg.split(' ', 1)[1]
                    self.handle_download(client, event, query, is_audio=False)
                    return

                if clean_msg.startswith("/img "):
                    query = msg.split(' ', 1)[1]
                    client.reply_message("🎨 Je prépare ton image... Un instant !", event)
                    res = self.ai.generate_image_from_text(query)
                    if res['status'] == 'success':
                        # Check if it's a local file or a URL
                        if res['url'].startswith('http'):
                            client.send_image(event.Info.Sender, res['url'], caption=f"🎨 Voici ton image : {query}")
                        else:
                            # Local file
                            client.send_image(event.Info.Sender, res['url'], caption=f"🎨 Voici ton image : {query}")
                            if os.path.exists(res['url']): os.remove(res['url'])
                    else:
                        client.reply_message(f"❌ Erreur image : {res.get('message')}", event)
                    return

                # Réponse IA (Vision ou Texte)
                from app.routes import process_command
                resp = process_command(user, msg, 'whatsapp')
                if resp and 'message' in resp and "Je n'ai pas compris" not in resp['message']:
                    client.reply_message(resp['message'], event)
                else:
                    client.reply_message("🤔 Laisse-moi réfléchir...", event)
                    ai_response = self.ai.chat(msg, image_path=image_path, mode=user.mode)
                    client.reply_message(ai_response, event)

                # Nettoyage image
                if image_path and os.path.exists(image_path): os.remove(image_path)

            except Exception as e:
                print(f"❌ Erreur on_message : {e}")

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
        
        # Enregistrement du gestionnaire de messages
        try:
            # On utilise le décorateur de manière explicite
            self.client.event(Message)(self.on_message)
            print("✅ Gestionnaire d'événements WhatsApp configuré.")
        except Exception as e:
            print(f"⚠️ Erreur lors de la configuration des événements : {e}")
            # Fallback pour d'autres versions
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
