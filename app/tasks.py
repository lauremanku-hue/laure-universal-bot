from celery import shared_task
from .extensions import db
from .models import User, Interaction, Course
from .modules.downloader import download_media
from .modules.whatsapp_handler import WhatsAppHandler
from .modules.telegram_handler import TelegramHandler
from datetime import datetime
import time

@shared_task(name="tasks.check_scheduled_courses")
def check_scheduled_courses():
    """Vérifie les cours à envoyer maintenant."""
    now = datetime.utcnow()
    courses = Course.query.filter(Course.scheduled_time <= now, Course.is_sent == False).all()
    
    wa = WhatsAppHandler()
    tg = TelegramHandler()
    
    for course in courses:
        print(f"📅 Envoi du cours programmé : {course.id}")
        message = f"🎓 *DÉBUT DU COURS PROGRAMMÉ*\n\n{course.content}\n\n_Posez vos questions, je suis là pour y répondre !_"
        
        if course.platform == 'whatsapp':
            wa.send_text(course.target_group, message)
        elif course.platform == 'telegram':
            tg.send_message(course.target_group, message)
            
        course.is_sent = True
        db.session.commit()
    
    return f"{len(courses)} cours envoyés."

@shared_task(name="tasks.process_download_task")
def process_download_task(url, user_whatsapp_id):
    """Téléchargement en arrière-plan pour ne pas bloquer le webhook."""
    print(f"📥 Début du téléchargement pour {user_whatsapp_id} : {url}")
    result = download_media(url)
    
    if result["status"] == "success":
        # Ici on appellerait l'API WhatsApp pour envoyer le fichier
        print(f"✅ Prêt à envoyer : {result['file_path']}")
    else:
        print(f"❌ Erreur : {result['message']}")
    return result

@shared_task(name="tasks.auto_reply_check")
def auto_reply_check(user_id):
    """
    Vérifie après 2 minutes si l'utilisateur a reçu une réponse.
    Si l'interaction est toujours 'pending', on envoie une relance.
    """
    from .models import Interaction
    # On attend un peu pour simuler le délai de 2 min dans les tests si nécessaire
    # Dans la vraie vie, Celery gère le countdown
    interaction = Interaction.query.filter_by(user_id=user_id, status='pending').order_by(Interaction.timestamp.desc()).first()
    
    if interaction:
        print(f"🤖 Relance automatique pour l'utilisateur {user_id}")
        interaction.status = 'auto_replied'
        db.session.commit()
        return "Relance envoyée"
    return "Déjà traité"

