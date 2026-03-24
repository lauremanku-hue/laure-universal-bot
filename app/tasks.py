import os
import threading
import time
from celery import shared_task
from .extensions import db
from .models import User, Interaction
from .modules.downloader import download_media

def run_delayed_reply(app, user_id, platform_id, original_msg, platform):
    """Exécute la relance après un délai dans un thread séparé."""
    with app.app_context():
        time.sleep(180) # Attendre 3 minutes
        auto_reply_task(user_id, platform_id, original_msg, platform)

def schedule_download_task(app, url, user_platform_id, is_audio=False, platform='whatsapp'):
    """Tente de planifier via Celery, sinon utilise un thread de secours."""
    try:
        process_download_task.apply_async(args=[url, user_platform_id, is_audio, platform])
        print(f"✅ Tâche téléchargement planifiée via Celery pour {user_platform_id}")
    except Exception as e:
        print(f"⚠️ Celery/Redis indisponible ({e}). Utilisation du thread de secours pour le téléchargement.")
        thread = threading.Thread(target=run_download_thread, args=(app, url, user_platform_id, is_audio, platform))
        thread.daemon = True
        thread.start()

def run_download_thread(app, url, user_platform_id, is_audio, platform):
    """Exécute le téléchargement dans un thread séparé."""
    with app.app_context():
        process_download_task(url, user_platform_id, is_audio, platform)

@shared_task(name="tasks.process_download_task")
def process_download_task(url, user_platform_id, is_audio=False, platform='whatsapp'):
    """Tâche de téléchargement asynchrone."""
    import os
    from .modules.whatsapp_handler import WhatsAppHandler
    from .modules.telegram_handler import TelegramHandler
    
    wa = WhatsAppHandler()
    tg = TelegramHandler()

    print(f"📥 Téléchargement {'audio' if is_audio else 'vidéo'} pour {user_platform_id}")
    try:
        res = download_media(url, is_audio=is_audio)
        if res['status'] == 'success':
            file_path = res['file_path']
            media_type = 'audio' if is_audio else 'video'
            
            if platform == 'whatsapp':
                send_res = wa.send_local_media(user_platform_id, file_path, media_type)
                if 'error' in send_res or 'errors' in send_res:
                    print(f"❌ Erreur envoi WhatsApp: {send_res}")
                    wa.send_text(user_platform_id, f"❌ Erreur lors de l'envoi du fichier à WhatsApp : {send_res}")
            elif platform == 'telegram':
                tg.send_local_file(user_platform_id, file_path, media_type)
            
            # Optionnel : Supprimer le fichier après envoi pour économiser de l'espace
            if os.path.exists(file_path):
                os.remove(file_path)
            return "Success"
        else:
            error_msg = f"❌ Erreur lors du téléchargement : {res.get('message', 'Inconnu')}"
            if platform == 'whatsapp':
                wa.send_text(user_platform_id, error_msg)
            elif platform == 'telegram':
                tg.send_message(user_platform_id, error_msg)
            return "Error: " + res.get('message', 'Unknown')
    except Exception as e:
        error_msg = f"❌ Erreur système lors du téléchargement : {str(e)}"
        if platform == 'whatsapp':
            wa.send_text(user_platform_id, error_msg)
        elif platform == 'telegram':
            tg.send_message(user_platform_id, error_msg)
        print(f"❌ Erreur téléchargement: {e}")
        return None

@shared_task(name="tasks.auto_reply_task")
def auto_reply_task(user_id, platform_id, original_msg, platform):
    """Vérifie si l'utilisateur a répondu, sinon envoie une réponse auto après 3 min."""
    from .models import Interaction, User
    from .modules.ai_handler import AIHandler
    from .modules.whatsapp_handler import WhatsAppHandler
    from .modules.telegram_handler import TelegramHandler

    try:
        # Vérifier si une nouvelle interaction a eu lieu depuis le message original
        user = User.query.get(user_id)
        if not user: return "User not found"

        # On récupère la dernière interaction
        last_int = Interaction.query.filter_by(user_id=user_id).order_by(Interaction.timestamp.desc()).first()
        
        if last_int and last_int.status == 'pending':
            # L'utilisateur n'a pas encore eu de réponse de Laure ou n'a pas relancé
            ai = AIHandler()
            wa = WhatsAppHandler()
            tg = TelegramHandler()

            # Générer une réponse basée sur l'humeur et le message
            prompt = f"L'utilisateur a envoyé : '{original_msg}'. Il n'a pas répondu depuis 3 minutes. Envoie une relance amicale, drôle ou intrigante en fonction de son message pour le faire revenir discuter. Sois Laure."
            reply = ai.generate_text(prompt)

            if platform == 'whatsapp' and wa:
                wa.send_text(platform_id, f"✨ *RELANCE AUTOMATIQUE* ✨\n\n{reply}")
            elif platform == 'telegram' and tg:
                tg.send_message(platform_id, f"✨ *RELANCE AUTOMATIQUE* ✨\n\n{reply}")
            
            last_int.status = 'auto_replied'
            db.session.commit()
            return "Auto-réponse envoyée"
    except Exception as e:
        print(f"❌ Erreur auto_reply_task: {e}")
    
    return "L'utilisateur a déjà répondu ou a été servi"

def schedule_auto_reply(app, user_id, platform_id, original_msg, platform):
    """Tente de planifier via Celery, sinon utilise un thread de secours."""
    try:
        # On tente Celery (nécessite Redis)
        auto_reply_task.apply_async(args=[user_id, platform_id, original_msg, platform], countdown=180)
        print("✅ Tâche auto-réponse planifiée via Celery.")
    except Exception as e:
        print(f"⚠️ Celery/Redis indisponible ({e}). Utilisation du thread de secours.")
        # Fallback sur un thread (ne bloque pas le serveur)
        thread = threading.Thread(target=run_delayed_reply, args=(app, user_id, platform_id, original_msg, platform))
        thread.daemon = True
        thread.start()

@shared_task(name="tasks.send_scheduled_courses")
def send_scheduled_courses():
    """Vérifie et envoie les cours programmés."""
    from .models import Course, User
    from .modules.whatsapp_handler import WhatsAppHandler
    from .modules.telegram_handler import TelegramHandler
    from datetime import datetime

    now = datetime.utcnow()
    # On récupère les cours non envoyés dont l'heure est passée
    pending_courses = Course.query.filter_by(is_sent=False).filter(Course.scheduled_time <= now).all()
    
    wa = WhatsAppHandler()
    tg = TelegramHandler()

    for course in pending_courses:
        try:
            msg = f"🎓 *COURS PROGRAMMÉ* 🎓\n\n{course.content}"
            if course.platform == 'whatsapp' and wa:
                wa.send_text(course.target_group, msg)
            elif course.platform == 'telegram' and tg:
                tg.send_message(course.target_group, msg)
            
            course.is_sent = True
            db.session.commit()
            print(f"✅ Cours {course.id} envoyé à {course.target_group}")
        except Exception as e:
            print(f"❌ Erreur envoi cours {course.id}: {e}")
