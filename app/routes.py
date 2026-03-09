
import os
from flask import Blueprint, request, jsonify, make_response
from datetime import datetime, timedelta

from .extensions import db
from .models import User, Interaction, Subscription, Course
from .modules.ai_handler import AIHandler
from .modules.telegram_handler import TelegramHandler
from .modules.whatsapp_handler import WhatsAppHandler
from .modules.downloader import validate_url
from .tasks import process_download_task

main = Blueprint('main', __name__)

def send_data_bonus(phone, network):
    """
    Simule l'envoi du bonus de 500 Mo.
    En production, ceci appellerait une API de recharge.
    """
    print(f"📡 Envoi de 500 Mo au {phone} sur le réseau {network}")
    return True

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
    # Logique d'interaction
    new_int = Interaction(user_id=user.id, last_message=msg)
    db.session.add(new_int)
    db.session.commit()

    # Infos de contact
    contact_info = "\n\n📧 Contact : laure.support@example.com\n📱 WhatsApp : +229 00000000"

    # 1. MENU & AIDE
    if msg.lower() in ['aide', 'menu', '/start', '/menu']:
        menu_text = (
            "🚀 *MENU LAURE - VOTRE ASSISTANT UNIVERSEL*\n\n"
            "Bonjour ! Je suis Laure, votre assistant IA multi-plateformes.\n\n"
            "*COMMANDES DISPONIBLES :*\n"
            "🎨 `/img <texte>` : Générer une image par IA\n"
            "📥 *Envoyez un lien* (YouTube/FB/IG) : Télécharger la vidéo\n"
            "💳 `/pay` : Devenir membre Premium\n"
            "❓ *Posez-moi n'importe quelle question !*"
            f"{contact_info}"
        )
        return {"message": menu_text}

    # 1.5 COMMANDE ADMIN (Réservée)
    elif msg.lower() == '/admin':
        admin_id = os.getenv("ADMIN_ID")
        if user.platform_id == admin_id:
            total_users = User.query.count()
            premium_users = User.query.filter(User.is_premium_member == True).count()
            total_interactions = Interaction.query.count()
            
            stats = (
                "📊 *TABLEAU DE BORD ADMIN*\n\n"
                f"👥 Utilisateurs totaux : {total_users}\n"
                f"💎 Membres Premium : {premium_users}\n"
                f"💬 Interactions totales : {total_interactions}\n\n"
                "✅ Laure fonctionne parfaitement !"
            )
            return {"message": stats}
        else:
            return {"message": "🚫 Commande réservée à l'administrateur."}

    # 2. PAIEMENT
    elif msg.lower() == '/pay':
        service_id = os.getenv("MONETBIL_SERVICE_ID", "votre_id_ici")
        payment_url = f"https://www.monetbil.com/pay/v2.1/{service_id}?amount=100&phone={user.platform_id}&externalId={user.id}"
        return {"message": f"💳 *DEVENIR PREMIUM*\n\nAccédez au téléchargement illimité, à la génération d'images HD et recevez *500 Mo de BONUS* (MTN/Orange) !\n\n🔗 *Lien de paiement sécurisé* : {payment_url}\n\n_Une fois payé, votre compte sera activé instantanément._"}

    # 3. IA IMAGE (Premium Check)
    elif msg.startswith('/img '):
        if not user.is_premium:
            return {"message": "❌ *ACCÈS PREMIUM REQUIS*\n\nCette fonctionnalité est réservée aux abonnés. Tapez */pay* pour activer votre accès !"}
        if ai:
            prompt = msg.replace('/img ', '')
            res = ai.generate_image_from_text(prompt)
            return {"message": f"🎨 Image générée pour : {prompt}\nLien : {res.get('url')}"}
        return {"message": "Moteur d'image indisponible."}

    # 4. TÉLÉCHARGEMENT VIDÉO (Premium Check)
    elif validate_url(msg):
        if not user.is_premium:
            return {"message": "❌ *ACCÈS PREMIUM REQUIS*\n\nLe téléchargement de vidéos est réservé aux abonnés. Tapez */pay* pour profiter de Laure en illimité !"}
        process_download_task.delay(msg, user.platform_id)
        return {"message": "📥 Lien reçu ! Analyse en cours..."}

    # 5. IA UNIVERSELLE (Répond à tout le reste)
    else:
        if ai:
            # On demande à l'IA de répondre de manière pédagogique et amicale
            response = ai.generate_text(f"Réponds en tant que Laure, une assistante IA intelligente et amicale. Question de l'utilisateur : {msg}")
            return {"message": response}
        return {"message": f"🤖 Laure a bien reçu : \"{msg}\". Tapez /menu pour voir mes options !"}

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
                # Gestion Messenger / Instagram
                if 'messaging' in entry:
                    for messaging_event in entry['messaging']:
                        sender_id = messaging_event['sender']['id']
                        if 'message' in messaging_event and 'text' in messaging_event['message']:
                            text = messaging_event['message']['text']
                            platform = 'instagram' if 'instagram' in str(entry).lower() else 'messenger'
                            user = User.query.filter_by(platform=platform, platform_id=sender_id).first()
                            if not user:
                                user = User(platform=platform, platform_id=sender_id, name=f"User {platform.capitalize()}", bonus_given=True)
                                db.session.add(user)
                                db.session.commit()
                            resp = process_command(user, text, platform)
                            # Envoi réponse (à implémenter selon MetaHandler)
                
                # Gestion WhatsApp
                elif 'changes' in entry:
                    value = entry['changes'][0]['value']
                    if 'messages' in value:
                        msg = value['messages'][0]
                        sender = msg['from']
                        text = msg.get('text', {}).get('body', '')

                        user = User.query.filter_by(platform='whatsapp', platform_id=sender).first()
                        if not user:
                            user = User(platform='whatsapp', platform_id=sender, name="Utilisateur WA", bonus_given=True)
                            db.session.add(user)
                            db.session.commit()
                            welcome_msg = "🌟 *BIENVENUE CHEZ LAURE !* 🌟\n\nMerci de m'avoir contactée ! Tu as reçu un *bonus de 100 FCFA* pour tester mes services.\n\nTape *menu* pour voir tout ce que je peux faire pour toi !"
                            if wa_handler: wa_handler.send_text(sender, welcome_msg)

                        resp = process_command(user, text, 'whatsapp')
                        if wa_handler: wa_handler.send_text(sender, resp['message'])
    except Exception as e:
        print(f"❌ Erreur Webhook Meta: {e}")

    return jsonify({"status": "ok"}), 200

@main.route('/webhook/monetbil', methods=['POST'])
def monetbil_webhook():
    data = request.form
    status = data.get('status')
    amount = data.get('amount')
    user_id = data.get('externalId')
    phone = data.get('phone')
    operator = data.get('operator') # MTN ou ORANGE

    if status == 'success':
        user = User.query.get(user_id)
        if user:
            user.is_premium_member = True
            
            # Gestion du bonus de 500 Mo
            bonus_msg = ""
            if not user.data_bonus_given and operator in ['MTN', 'ORANGE']:
                if send_data_bonus(phone, operator):
                    user.data_bonus_given = True
                    bonus_msg = "\n\n🎁 *CADEAU* : Tes 500 Mo de bonus ont été envoyés sur ton numéro !"

            db.session.commit()

            # Notification au bot
            msg = f"✅ *PAIEMENT REÇU !*\n\nMerci ! Ton compte est maintenant *PREMIUM*. Profite bien de Laure !{bonus_msg}"
            if user.platform == 'whatsapp' and wa_handler:
                wa_handler.send_text(user.platform_id, msg)
            elif user.platform == 'telegram' and tg:
                tg.send_message(user.platform_id, msg)

    return "OK", 200

@main.route('/payment/success')
def payment_success():
    return "<h1>Paiement réussi !</h1><p>Vous pouvez retourner sur WhatsApp/Telegram.</p>"

@main.route('/payment/fail')
def payment_fail():
    return "<h1>Paiement échoué</h1><p>Veuillez réessayer ou contacter le support.</p>"

@main.route('/privacy')
@main.route('/privacy/')
def privacy():
    return """
    <!DOCTYPE html>
    <html lang="fr">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Politique de Confidentialité - Laure Bot</title>
        <style>
            body { font-family: sans-serif; line-height: 1.6; max-width: 800px; margin: 40px auto; padding: 0 20px; color: #333; }
            h1 { color: #2c3e50; }
            .date { color: #7f8c8d; font-style: italic; }
        </style>
    </head>
    <body>
        <h1>Politique de Confidentialité - Laure Bot</h1>
        <p class="date">Dernière mise à jour : 09 Mars 2026</p>
        <p>Laure Bot est un service d'assistance par intelligence artificielle. Nous accordons une grande importance à la protection de vos données personnelles.</p>
        
        <h2>1. Collecte des données</h2>
        <p>Nous collectons uniquement les informations strictement nécessaires au fonctionnement du service :</p>
        <ul>
            <li>Votre identifiant de plateforme (WhatsApp ID ou Telegram ID).</li>
            <li>Le contenu des messages que vous envoyez au bot pour permettre à l'IA de vous répondre.</li>
        </ul>

        <h2>2. Utilisation des données</h2>
        <p>Vos données sont utilisées exclusivement pour :</p>
        <ul>
            <li>Générer des réponses personnalisées via l'IA.</li>
            <li>Gérer votre abonnement Premium le cas échéant.</li>
        </ul>

        <h2>3. Partage des données</h2>
        <p>Nous ne vendons, ne louons et ne partageons jamais vos données personnelles avec des tiers à des fins commerciales.</p>

        <h2>4. Contact</h2>
        <p>Pour toute question, vous pouvez nous contacter à l'adresse e-mail de support indiquée dans le menu du bot.</p>
    </body>
    </html>
    """

@main.route('/webhook/telegram', methods=['POST'])
def telegram_webhook():
    data = request.json
    if data and "message" in data:
        chat_id = str(data["message"]["chat"]["id"])
        text = data["message"].get("text", "")
        
        user = User.query.filter_by(platform='telegram', platform_id=chat_id).first()
        if not user:
            user = User(platform='telegram', platform_id=chat_id, name="User TG", bonus_given=True)
            db.session.add(user)
            db.session.commit()
            welcome_msg = "🌟 *BIENVENUE CHEZ LAURE SUR TELEGRAM !* 🌟\n\nTu as reçu un *bonus de 100 FCFA*.\n\nTape *menu* pour commencer !"
            if tg: tg.send_message(chat_id, welcome_msg)

        resp = process_command(user, text, 'telegram')
        if tg: tg.send_message(chat_id, resp['message'])
            
    return jsonify({"status": "ok"}), 200

