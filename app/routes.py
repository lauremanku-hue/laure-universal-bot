import os
from flask import Blueprint, request, jsonify, make_response
from datetime import datetime, timedelta

from .extensions import db
from .models import User, Interaction, Course
from .modules.ai_handler import AIHandler
from .modules.telegram_handler import TelegramHandler
from .modules.whatsapp_handler import WhatsAppHandler
from .modules.downloader import validate_url
from .tasks import process_download_task

main = Blueprint('main', __name__)

# Initialisation sécurisée des handlers
try:
    ai = AIHandler()
    tg = TelegramHandler()
    wa_handler = WhatsAppHandler()
    print("✅ Handlers (AI, Telegram, WhatsApp) opérationnels.")
except Exception as e:
    print(f"⚠️ Erreur initialisation Handlers : {e}")
    ai = None
    tg = None
    wa_handler = None

def process_command(user, msg, platform):
    """Cerveau du bot : traite les messages et décide de la réponse."""
    new_int = Interaction(user_id=user.id, last_message=msg)
    db.session.add(new_int)
    db.session.commit()

    # Infos de contact
    contact_info = "\n\n📧 Contact : laure.support@example.com\n📱 WhatsApp : +229 00000000"

    if msg.lower() in ['aide', 'menu', '/start', '/menu']:
        menu_text = (
            "🚀 *MENU LAURE - VOTRE ASSISTANT UNIVERSEL*\n\n"
            "Bonjour ! Je suis Laure, votre assistant IA multi-plateformes.\n\n"
            "*COMMANDES DISPONIBLES :*\n"
            "🎨 `/img <texte>` : Générer une image par IA\n"
            "📥 *Envoyez un lien* (YouTube/FB/IG) : Télécharger la vidéo\n"
            "📅 `/cours <contenu> | <heure>` : Programmer un cours (ex: `/cours Introduction à l'IA | 2026-02-21 10:00`)\n"
            "💳 `/pay` : Devenir membre Premium\n"
            "❓ *Posez-moi n'importe quelle question !*"
            f"{contact_info}"
        )
        return {"message": menu_text}

    elif msg.startswith('/img '):
        if ai:
            prompt = msg.replace('/img ', '')
            res = ai.generate_image_from_text(prompt)
            return {"message": f"🎨 Image générée pour : {prompt}\nLien : {res.get('url')}"}
        return {"message": "Moteur d'image indisponible."}

    elif msg.startswith('/cours '):
        try:
            parts = msg.replace('/cours ', '').split('|')
            if len(parts) < 2:
                return {"message": "❌ Format invalide. Utilisez : `/cours Contenu | AAAA-MM-JJ HH:MM`"}
            
            content = parts[0].strip()
            time_str = parts[1].strip()
            scheduled_time = datetime.strptime(time_str, '%Y-%m-%d %H:%M')
            
            target_group = user.platform_id
            
            new_course = Course(
                user_id=user.id,
                content=content,
                target_group=target_group,
                scheduled_time=scheduled_time,
                platform=platform
            )
            db.session.add(new_course)
            db.session.commit()
            
            return {"message": f"✅ Cours programmé pour le {time_str} !\nSujet : {content}"}
        except Exception as e:
            return {"message": f"❌ Erreur de format : {str(e)}"}

    elif validate_url(msg):
        process_download_task.delay(msg, user.platform_id)
        return {"message": "📥 Lien reçu ! Analyse en cours..."}

    # Logique pour répondre aux questions sur le cours
    recent_course = Course.query.filter_by(target_group=user.platform_id, is_sent=True).order_by(Course.scheduled_time.desc()).first()
    if recent_course:
        if (datetime.utcnow() - recent_course.scheduled_time).total_seconds() < 3600:
            if ai:
                prompt = f"L'utilisateur pose une question sur le cours suivant : '{recent_course.content}'. Question : '{msg}'. Réponds de manière pédagogique en tant que Laure."
                response = ai.generate_text(prompt)
                return {"message": f"🎓 *Réponse au cours* :\n\n{response}"}

    return {"message": f"🤖 Laure a reçu votre message : \"{msg}\"\nTapez `/menu` pour voir ce que je peux faire !"}

@main.route('/webhook/meta', methods=['GET', 'POST'])
def whatsapp_webhook():
    if request.method == 'GET':
        mode = request.args.get("hub.mode")
        token_recu = request.args.get("hub.verify_token")
        challenge = request.args.get("hub.challenge")
        token_attendu = os.getenv("VERIFY_TOKEN", "laure_secret")
        if mode == "subscribe" and token_recu == token_attendu:
            return make_response(str(challenge), 200)
        return "Forbidden", 403

    data = request.json
    try:
        if data and 'entry' in data:
            for entry in data['entry']:
                if 'messaging' in entry:
                    for messaging_event in entry['messaging']:
                        sender_id = messaging_event['sender']['id']
                        if 'message' in messaging_event and 'text' in messaging_event['message']:
                            text = messaging_event['message']['text']
                            platform = 'instagram' if 'instagram' in str(entry).lower() else 'messenger'
                            user = User.query.filter_by(platform=platform, platform_id=sender_id).first()
                            is_new = False
                            if not user:
                                user = User(platform=platform, platform_id=sender_id, name=f"User {platform.capitalize()}")
                                db.session.add(user)
                                db.session.commit()
                                is_new = True
                            resp = process_command(user, text, platform)
                            if is_new:
                                intro = "👋 Bonjour ! Je suis *Laure*, votre nouvel assistant intelligent.\nTapez `/menu` pour découvrir mes super-pouvoirs !"
                                if platform == 'whatsapp' and wa_handler:
                                    wa_handler.send_text(sender_id, intro)
                elif 'changes' in entry:
                    value = entry['changes'][0]['value']
                    if 'messages' in value:
                        msg = value['messages'][0]
                        sender = msg['from']
                        text = msg.get('text', {}).get('body', '')
                        user = User.query.filter_by(platform='whatsapp', platform_id=sender).first()
                        is_new = False
                        if not user:
                            user = User(platform='whatsapp', platform_id=sender, name="User WA")
                            db.session.add(user)
                            db.session.commit()
                            is_new = True
                        if is_new:
                            intro = "👋 Bonjour ! Je suis *Laure*, votre nouvel assistant intelligent sur WhatsApp.\nTapez `/menu` pour voir ce que je peux faire pour vous !"
                            if wa_handler: wa_handler.send_text(sender, intro)
                        resp = process_command(user, text, 'whatsapp')
                        if wa_handler: wa_handler.send_text(sender, resp['message'])
    except Exception as e:
        print(f"❌ Erreur Webhook Meta: {e}")
    return jsonify({"status": "ok"}), 200

@main.route('/webhook/telegram', methods=['POST'])
def telegram_webhook():
    data = request.json
    if data and "message" in data:
        chat_id = str(data["message"]["chat"]["id"])
        text = data["message"].get("text", "")
        user = User.query.filter_by(platform='telegram', platform_id=chat_id).first()
        is_new = False
        if not user:
            user = User(platform='telegram', platform_id=chat_id, name="User TG")
            db.session.add(user)
            db.session.commit()
            is_new = True
        if is_new:
            intro = "👋 Bonjour ! Je suis *Laure*, votre nouvel assistant intelligent sur Telegram.\nTapez `/menu` pour voir ce que je peux faire pour vous !"
            if tg: tg.send_message(chat_id, intro)
        resp = process_command(user, text, 'telegram')
        if tg: tg.send_message(chat_id, resp['message'])
    return jsonify({"status": "ok"}), 200
