from celery import shared_task
from .extensions import db
from .models import User, Interaction
from .modules.downloader import download_media

@shared_task(name="tasks.process_download_task")
def process_download_task(url, user_whatsapp_id):
    """Tâche de téléchargement asynchrone."""
    print(f"📥 Téléchargement pour {user_whatsapp_id}")
    return download_media(url)

@shared_task(name="tasks.auto_reply_task")
def auto_reply_task(user_id, platform_id, original_msg, platform):
    """Vérifie si l'utilisateur a répondu, sinon envoie une réponse auto après 3 min."""
    from .models import Interaction, User
    from .modules.ai_handler import AIHandler
    from .modules.whatsapp_handler import WhatsAppHandler
    from .modules.telegram_handler import TelegramHandler
    import time

    # On attend 3 minutes (180 secondes)
    # Note: Dans un environnement réel, on utiliserait Celery countdown, mais ici on simule
    
    # Vérifier si une nouvelle interaction a eu lieu depuis le message original
    # On cherche s'il y a eu un message de l'utilisateur (last_message != original_msg)
    # ou si le statut est passé à 'replied'
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

        if platform == 'whatsapp':
            wa.send_text(platform_id, f"✨ *RELANCE AUTOMATIQUE* ✨\n\n{reply}")
        elif platform == 'telegram':
            tg.send_message(platform_id, f"✨ *RELANCE AUTOMATIQUE* ✨\n\n{reply}")
        
        last_int.status = 'auto_replied'
        db.session.commit()
        return "Auto-réponse envoyée"
    
    return "L'utilisateur a déjà répondu ou a été servi"
