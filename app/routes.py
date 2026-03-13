import os
import json
import random
from flask import Blueprint, request, jsonify, make_response
from datetime import datetime, timedelta

from .extensions import db
from .models import User, Interaction, Subscription, Course
from .modules.ai_handler import AIHandler
from .modules.telegram_handler import TelegramHandler
from .modules.whatsapp_handler import WhatsAppHandler
from .modules.downloader import validate_url
from .tasks import process_download_task, auto_reply_task

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

def handle_wizard(user, msg, msg_clean):
    """Gère les étapes de configuration d'un cours automatique."""
    state = user.current_state
    data = json.loads(user.state_data) if user.state_data else {}

    if state == 'awaiting_course_content':
        data['content'] = msg
        user.state_data = json.dumps(data)
        user.current_state = 'awaiting_course_group'
        db.session.commit()
        return {"message": "✅ Contenu reçu !\n\nÉtape 2 : Quel est le *nom exact* du groupe ou du canal où je dois poster ce cours ?"}

    elif state == 'awaiting_course_group':
        data['group'] = msg
        user.state_data = json.dumps(data)
        user.current_state = 'awaiting_course_time'
        db.session.commit()
        return {"message": "✅ Groupe enregistré !\n\nÉtape 3 : À quelle *heure* dois-je l'envoyer ? (Format HH:MM, ex: 14:30)"}

    elif state == 'awaiting_course_time':
        try:
            # Validation sommaire de l'heure
            time_parts = msg.split(':')
            if len(time_parts) != 2: raise ValueError()
            
            # Création du cours dans la DB
            new_course = Course(
                user_id=user.id,
                content=data['content'],
                target_group=data['group'],
                scheduled_time=datetime.utcnow() + timedelta(hours=1), # Simplification pour le test
                platform=user.platform
            )
            db.session.add(new_course)
            
            # Reset de l'état
            user.current_state = 'idle'
            user.state_data = None
            db.session.commit()
            
            return {"message": f"🎉 *CONFIGURATION TERMINÉE !* 🎉\n\nLe cours sur '{data['content'][:20]}...' sera envoyé dans le groupe *{data['group']}*.\n\nJe répondrai aussi aux questions des membres à la fin du cours !"}
        except:
            return {"message": "❌ Format d'heure invalide. Réessaie (ex: 14:30) ou tape 'annuler'."}
    
    if msg_clean == 'annuler':
        user.current_state = 'idle'
        user.state_data = None
        db.session.commit()
        return {"message": "Configuration annulée."}

    return {"message": "Je n'ai pas compris. Tape 'annuler' pour recommencer."}

def process_command(user, msg, platform):
    """Cerveau du bot : traite les messages et décide de la réponse."""
    # Nettoyage des préfixes courants (ex: /Laure, Laure,)
    msg_clean = msg.strip().lower()
    prefixes = ['/laure ', 'laure ', 'laure, ', '/laure, ']
    for pref in prefixes:
        if msg_clean.startswith(pref):
            msg_clean = msg_clean.replace(pref, '', 1)
            break
            
    print(f"🛠️ Debug Command: user={user.platform_id}, msg='{msg}', clean='{msg_clean}', is_premium={user.is_premium}")
    
    # 0. GESTION DU GUIDE DE CONFIGURATION (WIZARD)
    if user.current_state != 'idle':
        return handle_wizard(user, msg, msg_clean)

    # 1. COMMANDES DE BASE (Toujours accessibles)
    is_base_command = msg_clean in [
        'aide', 'menu', '/start', '/menu', 'laure', 
        '/profil', 'profil', 'statut', 'mon profil', 
        '/pay', 'cadeau', '/cadeau', '/de', '/blague', '/fun'
    ] or msg_clean.startswith('/pay ') or msg_clean.startswith('/dl ')

    # 2. BLOCAGE SI ESSAI TERMINÉ
    if not user.is_premium and not is_base_command:
        return {"message": "🚫 *PÉRIODE D'ESSAI TERMINÉE* 🚫\n\nTes 3 jours d'essai gratuit sont finis. Pour continuer à discuter avec Laure et utiliser toutes ses fonctions, abonne-toi dès maintenant !\n\nTape */pay* pour voir les tarifs."}

    # Logique d'interaction
    new_int = Interaction(user_id=user.id, last_message=msg)
    db.session.add(new_int)
    db.session.commit()

    # Infos de contact
    contact_info = "\n\n📧 Contact : lauresontia659@gmail.com\n📱 WhatsApp : +237 686683246"

    # Alerte expiration (Notification à l'avance)
    warning = ""
    if not user.is_premium_member and user.trial_days_left == 1:
        warning = "\n\n⚠️ *RAPPEL* : Ton essai gratuit se termine dans moins de 24h ! Tape /pay pour ne pas être déconnecté."

    # --- NOUVELLES COMMANDES SLASH ---

    # JEU DE DÉ
    if msg_clean == '/de':
        result = random.randint(1, 6)
        faces = ["⚀", "⚁", "⚂", "⚃", "⚄", "⚅"]
        return {"message": f"🎲 *LANCER DE DÉ* 🎲\n\nLe dé s'arrête sur... *{result}* {faces[result-1]} !"}

    # BLAGUES
    elif msg_clean in ['/blague', 'blague']:
        if ai:
            res = ai.generate_text("Raconte une blague courte et drôle en français.")
            return {"message": f"😂 *LAURE RIGOLE* 😂\n\n{res}"}
        return {"message": "Je n'ai pas de blague en tête pour le moment !"}

    # CULTURE GÉNÉRALE TERRE
    elif msg_clean in ['/terre', 'terre', 'planète']:
        if ai:
            res = ai.generate_text("Donne un fait incroyable et éducatif sur la planète Terre.")
            return {"message": f"🌍 *NOTRE PLANÈTE* 🌍\n\n{res}"}
        return {"message": "La Terre est ronde, c'est tout ce que je sais pour l'instant !"}

    # TÉLÉCHARGEMENT VIDÉO
    elif msg_clean.startswith('/dl '):
        if not user.is_premium:
            return {"message": "❌ *ACCÈS PREMIUM REQUIS*\n\nLe téléchargement est réservé aux VIP. Tape /pay !"}
        url = msg.split(' ')[1]
        if validate_url(url):
            process_download_task.delay(url, user.platform_id)
            return {"message": "📥 *TÉLÉCHARGEMENT* 📥\n\nLien reçu ! Je prépare ta vidéo..."}
        return {"message": "❌ Lien invalide."}

    # COURS RAPIDE
    elif msg_clean.startswith('/cours ') or msg_clean.startswith('/cour '):
        if not user.is_premium:
            return {"message": "❌ *ACCÈS PREMIUM REQUIS*"}
        sujet = msg.split(' ', 1)[1]
        if ai:
            res = ai.generate_text(f"Donne un cours structuré, pédagogique et complet sur : {sujet}. Utilise des emojis.")
            return {"message": f"🎓 *COURS SUR {sujet.upper()}* 🎓\n\n{res}"}
        return {"message": "Je ne peux pas donner de cours pour le moment."}

    # CONFIGURATION COURS AUTOMATIQUE (WIZARD)
    elif msg_clean == '/config_cours':
        if not user.is_premium:
            return {"message": "❌ *ACCÈS PREMIUM REQUIS*"}
        user.current_state = 'awaiting_course_content'
        db.session.commit()
        return {"message": "📝 *CONFIGURATION COURS AUTO* 📝\n\nÉtape 1 : Quel est le *sujet* ou le *contenu* du cours que tu veux programmer ?"}

    # TÉLÉCHARGEMENT AUTO (Vues uniques / Médias groupes)
    elif msg_clean == '/dl_auto':
        if not user.is_premium:
            return {"message": "❌ *ACCÈS PREMIUM REQUIS*"}
        return {"message": "🔄 *MODE TÉLÉCHARGEMENT AUTO* 🔄\n\nActivé ! Laure va maintenant tenter de capturer automatiquement tous les médias (y compris les vues uniques) dans les groupes où elle est *ADMIN*."}

    # TÉLÉCHARGEMENT STATUTS
    elif msg_clean == '/status':
        if not user.is_premium:
            return {"message": "❌ *ACCÈS PREMIUM REQUIS*"}
        return {"message": "📲 *TÉLÉCHARGEMENT STATUTS* 📲\n\nEnvoie-moi le lien du statut ou le contact dont tu veux capturer le statut (WhatsApp, FB, Telegram). Laure s'en occupe !"}

    # 1. MENU & AIDE
    if msg_clean in ['aide', 'menu', '/start', '/menu', 'laure']:
        if user.is_premium:
            menu_text = (
                "💎 *MENU VIP LAURE* 💎\n\n"
                "Félicitations ! Tu es un membre **VIP**. Profite de toute ma puissance sans limites ! 🚀\n\n"
                "✨ *TES PRIVILÈGES :*\n"
                "━━━━━━━━━━━━━━━━━━━━\n"
                "🧠 *IA Illimitée* : Pose toutes tes questions sans fin.\n"
                "🎨 *Images* : Tape `/img ton idée` (Illimité)\n"
                "📥 *Téléchargements* : Tape `/dl [lien]`\n"
                "🎓 *Cours Express* : Tape `/cours [sujet]`\n"
                "📅 *Programmer Cours* : Tape `/config_cours`\n"
                "📥 *Auto-DL* : Tape `/dl_auto` (Vues uniques)\n"
                "📲 *Statuts* : Tape `/status` (WA, FB, TG)\n"
                "🎭 *Fun* : `/blague`, `/quiz`, `/de`, `/terre`\n"
                "👤 *Statut* : Tape `statut` pour voir tes infos\n"
                "━━━━━━━━━━━━━━━━━━━━\n"
                "📢 *PARTAGE LAURE* : Aide tes amis à découvrir Laure !"
                f"{contact_info}"
            )
        else:
            menu_text = (
                "🚀 *LAURE - TON ASSISTANTE IA TOUT-EN-UN* 🚀\n\n"
                "Salut ! Je suis Laure. Je suis là pour t'aider à apprendre, créer et t'amuser ! ✨\n\n"
                "💡 *CE QUE JE PEUX FAIRE POUR TOI :*\n"
                "━━━━━━━━━━━━━━━━━━━━\n"
                "🧠 *Répondre à tout* : Pose-moi n'importe quelle question !\n"
                "🎨 *Images* : Tape `/img ton idée` (VIP 💎)\n"
                "📥 *Télécharger* : Tape `/dl [lien]` (VIP 💎)\n"
                "🎓 *Cours* : Tape `/cours [sujet]` (VIP 💎)\n"
                "🎭 *Divertissement* : `/blague`, `/de`, `/terre`\n"
                "👤 *Mon Profil* : Tape `statut` pour voir tes bonus\n"
                "💎 *Devenir VIP* : Tape `/pay` pour l'illimité + 500 Mo offerts !\n"
                "━━━━━━━━━━━━━━━━━━━━\n"
                "📢 *PARTAGE LAURE* : Transfère ce message à tes amis !"
                f"{contact_info}"
            )
        return {"message": menu_text + warning}

    # 1.1 COMMANDE PROFIL / STATUT
    elif msg_clean in ['/profil', 'profil', 'statut', 'mon profil']:
        status = "💎 PREMIUM (Illimité)" if user.is_premium else "🆓 GRATUIT (Limité)"
        bonus_status = "✅ Reçu (100 FCFA)" if user.bonus_given else "❌ Non reçu"
        data_status = "✅ Envoyé (500 Mo)" if user.data_bonus_given else "⏳ En attente (Abonne-toi !)"
        
        trial_info = ""
        if user.trial_days_left > 0:
            trial_info = f"\n🎁 *Essai VIP* : {user.trial_days_left} jour(s) restant(s)"
        
        profil_text = (
            "👤 *TON PROFIL LAURE* 👤\n\n"
            f"🆔 *ID* : `{user.platform_id}`\n"
            f"🌟 *Statut* : {status}{trial_info}\n"
            "━━━━━━━━━━━━━━━━━━━━\n"
            f"💰 *Bonus Bienvenue* : {bonus_status}\n"
            f"📡 *Bonus Data* : {data_status}\n"
            "━━━━━━━━━━━━━━━━━━━━\n"
            "💡 _Tape /pay pour passer en Premium et débloquer toutes les fonctionnalités !_"
        )
        return {"message": profil_text + warning}

    # 1.2 COMMANDE CADEAU / PARRAINAGE
    elif msg_clean == '/cadeau':
        bot_number = os.getenv("PHONE_NUMBER_ID", "923436404197048") # Valeur par défaut si non trouvé
        referral_link = f"https://wa.me/{bot_number}?text=Menu"
        gift_text = (
            "🎁 *TES CADEAUX LAURE* 🎁\n\n"
            "✅ *Bonus de bienvenue* : 100 FCFA déjà crédités !\n"
            "🔥 *OFFRE SPÉCIALE* : Partage ton lien avec 5 amis et gagne *1 jour de Premium GRATUIT* !\n\n"
            f"🔗 *Ton lien de partage* : {referral_link}\n\n"
            "_Plus tu partages, plus Laure devient intelligente pour toi !_"
        )
        return {"message": gift_text}

    # 1.5 COMMANDE ADMIN (Réservée)
    elif msg_clean == '/admin':
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
    elif msg_clean == '/pay':
        plans_text = (
            "💎 *CHOISIS TON PLAN VIP LAURE* 💎\n\n"
            "Débloque tout le potentiel de Laure :\n"
            "━━━━━━━━━━━━━━━━━━━━\n"
            "1️⃣ *1 SEMAINE* : 500 FCFA\n"
            "👉 Tape `/pay 1` pour ce plan\n\n"
            "2️⃣ *2,5 SEMAINES* : 750 FCFA\n"
            "👉 Tape `/pay 2` pour ce plan\n\n"
            "3️⃣ *1 MOIS* : 1500 FCFA\n"
            "👉 Tape `/pay 3` pour ce plan\n"
            "━━━━━━━━━━━━━━━━━━━━\n"
            "🎁 *BONUS* : 500 Mo de DATA offerts pour chaque abonnement !\n\n"
            "⚠️ _Note : Après tes 3 jours d'essai, tu devras t'abonner pour continuer à utiliser ces services._"
        )
        return {"message": plans_text}

    # 2.5 COURS (Premium Check)
    elif msg_clean in ['/cours', 'cours', 'apprendre']:
        if not user.is_premium:
            return {"message": "❌ *ACCÈS PREMIUM REQUIS*\n\nLes cours interactifs sont réservés aux membres VIP. Tapez */pay* pour vous abonner !"}
        
        cours_text = (
            "🎓 *ACADÉMIE LAURE* 🎓\n\n"
            "Que souhaites-tu apprendre aujourd'hui ?\n"
            "━━━━━━━━━━━━━━━━━━━━\n"
            "1️⃣ *Informatique* (Python, Web, IA)\n"
            "2️⃣ *Langues* (Anglais, Espagnol)\n"
            "3️⃣ *Business* (Marketing, Vente)\n"
            "━━━━━━━━━━━━━━━━━━━━\n"
            "👉 _Dis-moi simplement : 'Laure, je veux un cours sur [sujet]'_"
        )
        return {"message": cours_text}

    # 2.6 DIVERTISSEMENT (Fun & Jeux)
    elif msg_clean in ['/fun', 'fun', 'divertissement', 'jeu', 'blague']:
        fun_text = (
            "🎭 *ESPACE DIVERTISSEMENT* 🎭\n\n"
            "Besoin d'une pause ? Laure est aussi là pour ça !\n"
            "━━━━━━━━━━━━━━━━━━━━\n"
            "😂 *Blagues* : Tape `Laure, raconte-moi une blague`\n"
            "🧠 *Quiz* : Tape `Laure, lance un quiz` pour tester tes connaissances\n"
            "💡 *Anecdotes* : Tape `Laure, donne-moi un fait incroyable`\n"
            "🖼️ *Stickers* : Envoie-moi une image et je la transformerai (VIP 💎)\n"
            "━━━━━━━━━━━━━━━━━━━━\n"
            "👉 _Amuse-toi bien avec Laure !_"
        )
        return {"message": fun_text + warning}

    elif msg_clean.startswith('/pay '):
        choice = msg_clean.split(' ')[1]
        service_id = os.getenv("MONETBIL_SERVICE_ID", "votre_id_ici")
        
        plans = {
            "1": {"amount": 500, "label": "1 Semaine"},
            "2": {"amount": 750, "label": "2,5 Semaines"},
            "3": {"amount": 1500, "label": "1 Mois"}
        }
        
        if choice in plans:
            plan = plans[choice]
            payment_url = f"https://www.monetbil.com/pay/v2.1/{service_id}?amount={plan['amount']}&phone={user.platform_id}&externalId={user.id}&item_name=Premium_{plan['label']}"
            return {"message": (
                f"💳 *PAIEMENT PLAN {plan['label'].upper()}*\n\n"
                f"💰 Montant : {plan['amount']} FCFA\n"
                f"🔗 *Lien sécurisé* : {payment_url}\n\n"
                "_Ton compte sera activé automatiquement après le paiement._"
            )}
        else:
            return {"message": "❌ Plan invalide. Tape `/pay` pour voir les options."}

    # 3. IA IMAGE (Premium Check)
    elif msg_clean.startswith('/img ') or msg_clean.startswith('img '):
        if not user.is_premium:
            return {"message": "❌ *ACCÈS PREMIUM REQUIS*\n\nCette fonctionnalité est réservée aux abonnés. Tapez */pay* pour activer votre accès !"}
        if ai:
            prompt = msg.replace('/img ', '').replace('/IMG ', '').replace('img ', '').replace('IMG ', '')
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
            # Vérifier s'il y a un cours récent envoyé par cet utilisateur ou pour cet utilisateur
            recent_course = Course.query.filter_by(user_id=user.id, is_sent=True).order_by(Course.scheduled_time.desc()).first()
            context = ""
            if recent_course:
                # Si le cours a été envoyé il y a moins de 2 heures, on l'utilise comme contexte
                from datetime import datetime
                if (datetime.utcnow() - recent_course.scheduled_time).total_seconds() < 7200:
                    context = f"Tu viens de donner un cours sur : {recent_course.content[:500]}... Utilise ce contexte pour répondre si la question porte sur le cours."

            prompt = f"Réponds en tant que Laure, une assistante IA intelligente et amicale. {context} Question de l'utilisateur : {msg}"
            response = ai.generate_text(prompt)
            return {"message": response + warning}
        return {"message": f"🤖 Laure a bien reçu : \"{msg}\". Tapez /menu pour voir mes options !" + warning}

@main.route('/webhook/meta', methods=['GET', 'POST'])
def whatsapp_webhook():
    if request.method == 'GET':
        mode = request.args.get("hub.mode")
        token_recu = request.args.get("hub.verify_token")
        challenge = request.args.get("hub.challenge")
        token_attendu = os.getenv("VERIFY_TOKEN", "laure_secret")
        
        print(f"🔍 Tentative de vérification Webhook : mode={mode}, token={token_recu}")
        
        if mode == "subscribe" and token_recu == token_attendu:
            print("✅ Webhook vérifié avec succès !")
            return make_response(str(challenge), 200)
        
        print("❌ Échec de la vérification Webhook (Token invalide)")
        return "Forbidden", 403

    data = request.json
    # print(f"📦 Payload reçu : {data}") # Optionnel : très verbeux
    try:
        if data and 'entry' in data:
            for entry in data['entry']:
                # Gestion WhatsApp
                if 'changes' in entry:
                    value = entry['changes'][0]['value']
                    if 'messages' in value:
                        msg = value['messages'][0]
                        sender = msg['from']
                        text = msg.get('text', {}).get('body', '')
                        
                        print(f"📩 Message reçu de {sender} : {text}")

                        user = User.query.filter_by(platform='whatsapp', platform_id=sender).first()
                        if not user:
                            print(f"🆕 Nouvel utilisateur WhatsApp : {sender}")
                            user = User(platform='whatsapp', platform_id=sender, name="Utilisateur WA", bonus_given=True)
                            db.session.add(user)
                            db.session.commit()
                            welcome_msg = (
                                "🌟 *BIENVENUE CHEZ LAURE !* 🌟\n\n"
                                "Merci de m'avoir contactée ! Tu as reçu un *bonus de 100 FCFA* pour tester mes services.\n\n"
                                "🎁 *OFFRE SPÉCIALE* : Je t'offre **3 JOURS d'accès VIP GRATUIT** ! 🎉\n"
                                "Profite des images IA, des téléchargements et des cours dès maintenant.\n\n"
                                "Tape *menu* pour voir tout ce que je peux faire pour toi !"
                            )
                            if wa_handler: 
                                res = wa_handler.send_text(sender, welcome_msg)
                                print(f"📤 Réponse bienvenue envoyée : {res}")

                        print(f"⚙️ Traitement de la commande pour {sender}...")
                        resp = process_command(user, text, 'whatsapp')
                        
                        # Déclencher l'auto-réponse après 3 minutes si pas de réponse
                        auto_reply_task.apply_async(args=[user.id, sender, text, 'whatsapp'], countdown=180)
                        
                        if wa_handler: 
                            res = wa_handler.send_text(sender, resp['message'])
                            print(f"📤 Réponse commande envoyée : {res}")
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
            <li>Votre numéro de téléphone lors des transactions de paiement pour la validation de l'abonnement Premium.</li>
        </ul>

        <h2>2. Utilisation des données</h2>
        <p>Vos données sont utilisées exclusivement pour :</p>
        <ul>
            <li>Générer des réponses personnalisées via l'IA.</li>
            <li>Traiter vos paiements de manière sécurisée via notre partenaire <strong>Monetbil</strong>.</li>
            <li>Gérer votre abonnement Premium et vos accès aux fonctionnalités avancées.</li>
        </ul>

        <h2>3. Partage des données</h2>
        <p>Nous ne vendons, ne louons et ne partageons jamais vos données personnelles avec des tiers à des fins commerciales.</p>

        <h2>4. Contact</h2>
        <p>Pour toute question, vous pouvez nous contacter à l'adresse e-mail de support indiquée dans le menu du bot.</p>
    </body>
    </html>
    """

@main.route('/download-app')
def download_app():
    # Cette route permettra aux utilisateurs de télécharger l'APK directement
    # Tu devras placer ton fichier laure_bot.apk dans le dossier /static/
    return """
    <h1>Télécharger Laure Bot</h1>
    <p>Cliquez sur le bouton ci-dessous pour télécharger l'application Android (APK).</p>
    <a href="/static/laure_bot.apk" style="padding: 10px 20px; background: #25D366; color: white; text-decoration: none; border-radius: 5px;">Télécharger l'APK</a>
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
        
        # Déclencher l'auto-réponse après 3 minutes si pas de réponse
        auto_reply_task.apply_async(args=[user.id, chat_id, text, 'telegram'], countdown=180)
        
        if tg: tg.send_message(chat_id, resp['message'])
            
    return jsonify({"status": "ok"}), 200
