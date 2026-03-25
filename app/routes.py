import os
import json
from flask import Blueprint, jsonify, request, render_template_string, current_app
from .models import User, MessageLog, QuizSession
from .extensions import db
from datetime import datetime, timedelta

main = Blueprint('main', __name__)

@main.route('/')
def index():
    bot = getattr(current_app, 'bot', None)
    pairing_code = getattr(bot, 'pairing_code', None) if bot else None
    
    from flask import make_response
    resp = make_response(render_template_string("""
    <!DOCTYPE html>
    <html>
    <head>
        <title>LAURE BOT - CONNEXION v1.2.4</title>
        <style>
            body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; text-align: center; padding: 20px; background: #f0f2f5; color: #1c1e21; }
            .card { background: white; padding: 40px; border-radius: 20px; box-shadow: 0 10px 30px rgba(0,0,0,0.1); display: inline-block; max-width: 450px; width: 100%; margin-top: 50px; }
            h1 { color: #25d366; margin-bottom: 20px; font-size: 2.2em; }
            .status-badge { padding: 8px 15px; border-radius: 20px; font-weight: bold; font-size: 0.9em; display: inline-block; margin-bottom: 25px; }
            .status-waiting { background: #fff3cd; color: #856404; }
            .status-pairing { background: #cce5ff; color: #004085; }
            
            .pairing-box { background: #f8f9fa; padding: 30px; border-radius: 15px; margin: 25px 0; border: 2px dashed #007bff; }
            .pairing-code { font-size: 3em; font-weight: 900; letter-spacing: 8px; color: #007bff; margin: 15px 0; font-family: monospace; }
            
            .input-group { margin: 30px 0; }
            input { padding: 15px; border-radius: 10px; border: 2px solid #ddd; width: 80%; font-size: 1.1em; outline: none; transition: border-color 0.3s; }
            
            .btn { background: #25d366; color: white; padding: 15px 30px; border-radius: 10px; text-decoration: none; display: inline-block; font-weight: bold; border: none; cursor: pointer; font-size: 1.1em; width: 80%; margin-top: 10px; }
            .btn-blue { background: #007bff; }
            
            .instructions { text-align: left; background: #fff; padding: 20px; border-radius: 12px; font-size: 0.95em; margin-top: 30px; border: 1px solid #eee; }
            .footer { margin-top: 40px; color: #888; font-size: 0.85em; }
        </style>
    </head>
    <body>
        <div class="card">
            <h1>🌟 Laure Bot</h1>
            
            {% if pairing_code %}
                <div class="status-badge status-pairing">📲 Code de couplage prêt</div>
                <div class="pairing-box">
                    <p>Entrez ce code sur votre WhatsApp :</p>
                    <div class="pairing-code">{{ pairing_code }}</div>
                </div>
            {% else %}
                <div class="status-badge status-waiting">⏳ En attente de connexion</div>
                <p>Entrez votre numéro pour connecter Laure.</p>
                
                <form action="/pair" method="POST" class="input-group">
                    <input type="text" name="phone" placeholder="Ex: 237690000000" required>
                    <button type="submit" class="btn btn-blue">Générer mon code</button>
                </form>
            {% endif %}

            <div class="instructions">
                <strong>💡 Note :</strong> Le bot démarre à la demande pour économiser les ressources.
            </div>
            
            <div class="footer">
                Laure Bot v1.2.4 | Port 3000 Forcé
            </div>
        </div>
    </body>
    </html>
    """, pairing_code=pairing_code))
    resp.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    resp.headers['Pragma'] = 'no-cache'
    resp.headers['Expires'] = '0'
    return resp

@main.route('/pair', methods=['GET', 'POST'])
def pair_with_phone():
    from flask import current_app, redirect, url_for, request
    if request.method == 'GET':
        return redirect(url_for('main.index'))
    
    phone = request.form.get('phone')
    if not phone:
        return redirect(url_for('main.index'))
    
    # Nettoyage du numéro
    phone = phone.replace('+', '').replace(' ', '')
    
    # Démarrage du bot UNIQUEMENT quand on demande un code
    bot = getattr(current_app, 'bot', None)
    if not bot:
        from app.modules.whatsapp_web import LaureWebBot
        import threading
        
        def start_bot_async(app_instance):
            with app_instance.app_context():
                try:
                    new_bot = LaureWebBot()
                    app_instance.bot = new_bot
                    new_bot.start(app=app_instance)
                except Exception as e:
                    print(f"❌ Erreur lors du démarrage du bot : {e}")
        
        # On passe l'instance réelle de l'application au thread
        thread = threading.Thread(target=start_bot_async, args=(current_app._get_current_object(),), daemon=True)
        thread.start()
        
        # On attend un tout petit peu que le bot s'initialise
        import time
        time.sleep(2)
        bot = getattr(current_app, 'bot', None)

    if bot:
        res = bot.get_pairing_code(phone)
        if res['status'] == 'success':
            return redirect(url_for('main.index'))
        else:
            return f"Erreur : {res['message']}. <a href='/'>Retour</a>"
    
    return redirect(url_for('main.index'))

@main.route('/api/monetbil/webhook', methods=['POST'])
def monetbil_webhook():
    """
    Handle Monetbil payment notifications.
    """
    data = request.form
    status = data.get('status')
    custom = data.get('custom') # Format: user_id:plan_type
    
    if status == 'success' and custom:
        try:
            user_id, plan_type = custom.split(':')
            user = User.query.get(int(user_id))
            if user:
                user.is_premium = True
                now = datetime.utcnow()
                if plan_type == 'day':
                    user.premium_ends_at = (user.premium_ends_at or now) + timedelta(days=1)
                elif plan_type == 'week':
                    user.premium_ends_at = (user.premium_ends_at or now) + timedelta(days=7)
                elif plan_type == 'month':
                    user.premium_ends_at = (user.premium_ends_at or now) + timedelta(days=30)
                
                db.session.commit()
                return jsonify({"status": "ok"}), 200
        except Exception as e:
            print(f"❌ Error processing Monetbil webhook: {e}")
            return jsonify({"status": "error", "message": str(e)}), 500

    return jsonify({"status": "ignored"}), 200

def process_command(user, msg, platform):
    """
    Process a command from a user and return a response.
    """
    clean_msg = msg.lower().strip()
    
    if clean_msg == 'menu':
        status = "✅ ESSAI ACTIF" if user.has_access() and not user.is_premium else "💎 VIP ACTIF" if user.is_premium else "❌ ACCÈS EXPIRÉ"
        return {
            "message": (
                f"🌟 *MENU DE LAURE* 🌟\n"
                f"Statut : {status}\n\n"
                "Voici ce que je peux faire pour toi :\n"
                "1. 🎨 *Image IA* : `/img <description>`\n"
                "2. 🎵 *Musique* : `/audio <recherche>`\n"
                "3. 🎓 *Aide aux Devoirs* : Envoie une photo ou tape `prof`.\n"
                "4. 📚 *Quiz Avancé* : `quiz <sujet>` (ex: `quiz histoire`)\n"
                "5. 🤔 *Devinette* : Tape `devinette`.\n"
                "6. 📅 *Programmer un Cours* : `/programme_cours Titre | HH:MM | Jour(0-6)`\n"
                "7. 📢 *Partager* : `/partager`.\n"
                "8. 💎 *VIP* : `vip` pour t'abonner."
            )
        }

    if clean_msg == '/partager':
        return {
            "message": (
                "📢 *AIDE-MOI À GRANDIR !* 📢\n\n"
                "Tu aimes mes services ? Partage-moi avec tes amis et reçois *50 FCFA* par ami qui s'inscrit !\n\n"
                "Copie et transfère ce message :\n"
                "---------------------------\n"
                "Salut ! J'utilise *Laure*, une IA incroyable sur WhatsApp qui aide pour les devoirs, génère des images et télécharge de la musique. Teste-la ici : https://wa.me/TON_NUMERO_BOT"
            )
        }
    
    if clean_msg == '/solde':
        now = datetime.utcnow()
        if user.is_premium:
            expiry = user.premium_ends_at.strftime("%d/%m/%Y %H:%M") if user.premium_ends_at else "Illimité"
            msg = f"💎 *STATUT VIP* : ✅ ACTIF\n📅 Expire le : {expiry}"
        else:
            expiry = user.trial_ends_at.strftime("%d/%m/%Y %H:%M") if user.trial_ends_at else "Expiré"
            msg = f"⏳ *STATUT ESSAI* : {'✅ ACTIF' if user.has_access() else '❌ EXPIRÉ'}\n📅 Fin de l'essai : {expiry}"
        
        return {"message": msg}
    
    if clean_msg == 'vip':
        return {
            "message": (
                "💎 *OFFRES VIP LAURE* 💎\n\n"
                "Deviens VIP pour profiter de Laure en illimité :\n"
                "- 🎨 Images IA illimitées\n"
                "- 🎵 Téléchargements Audio/Vidéo illimités\n"
                "- 🎓 Aide aux devoirs complète\n"
                "- 🚀 Réponses prioritaires\n\n"
                "Options :\n"
                "1. *Journée* : 200 FCFA\n"
                "2. *Semaine* : 1000 FCFA\n"
                "3. *Mois* : 3000 FCFA\n\n"
                "Tape *payer* pour obtenir ton lien de paiement sécurisé."
            )
        }
    
    if clean_msg == 'devinette':
        from app.modules.ai_handler import AIHandler
        ai = AIHandler()
        riddle = ai.get_riddle()
        # On stocke la réponse attendue dans une session temporaire ou on utilise un format spécifique
        return {
            "message": f"🤔 *DEVINETTE* :\n\n{riddle['question']}\n\n(Réponds pour voir si tu as juste !)"
        }

    if clean_msg.startswith('quiz '):
        topic = msg.split(' ', 1)[1]
        from app.modules.ai_handler import AIHandler
        ai = AIHandler()
        questions = ai.generate_quiz_questions(topic, count=20)
        if not questions:
            return {"message": "Désolé, je n'ai pas pu générer de quiz sur ce sujet."}
        
        session = QuizSession(
            group_id=user.platform_id, 
            status='active', 
            questions_data=json.dumps(questions),
            responses='[]',
            current_question_index=0,
            total_questions=len(questions),
            correct_answers_count=0
        )
        db.session.add(session)
        db.session.commit()
        
        q = questions[0]
        return {
            "message": (
                f"📚 *QUIZ : {topic.upper()}* (1/{len(questions)})\n\n"
                f"{q['q']}\n\n"
                f"A) {q['a']}\n"
                f"B) {q['b']}\n"
                f"C) {q['c']}\n"
                f"D) {q['d']}\n\n"
                "Réponds par A, B, C ou D."
            )
        }

    if clean_msg.startswith('/programme_cours '):
        # Format: /programme_cours Titre | HH:MM | Jour(0-6)
        try:
            parts = msg.split(' ', 1)[1].split('|')
            title = parts[0].strip()
            time_str = parts[1].strip()
            day = int(parts[2].strip())
            
            from .models import ScheduledCourse
            new_course = ScheduledCourse(
                user_id=user.id,
                title=title,
                target_jid=user.platform_id, # Par défaut au JID de l'utilisateur
                day_of_week=day,
                scheduled_time=time_str
            )
            db.session.add(new_course)
            db.session.commit()
            return {"message": f"✅ Cours sur *{title}* programmé pour chaque {['Lundi', 'Mardi', 'Mercredi', 'Jeudi', 'Vendredi', 'Samedi', 'Dimanche'][day]} à {time_str} !"}
        except:
            return {"message": "❌ Format invalide. Utilise : `/programme_cours Titre | HH:MM | Jour(0-6)`"}

    if clean_msg == 'payer':
        # Placeholder for Monetbil Service ID
        service_id = os.environ.get('MONETBIL_SERVICE_ID', 'YOUR_SERVICE_ID')
        # We can generate different links for different plans
        return {
            "message": (
                "💳 *PAIEMENT SÉCURISÉ MONETBIL* 💳\n\n"
                "Choisis ton forfait pour continuer à utiliser Laure :\n\n"
                f"1️⃣ *1 JOUR* (200 FCFA) :\n🔗 https://www.monetbil.com/pay/v2.1/{service_id}?amount=200&custom={user.id}:day\n\n"
                f"2️⃣ *1 SEMAINE* (1000 FCFA) :\n🔗 https://www.monetbil.com/pay/v2.1/{service_id}?amount=1000&custom={user.id}:week\n\n"
                f"3️⃣ *1 MOIS* (3000 FCFA) :\n🔗 https://www.monetbil.com/pay/v2.1/{service_id}?amount=3000&custom={user.id}:month\n\n"
                "✅ Ton compte sera activé *automatiquement* dès que le paiement est confirmé !"
            )
        }
    
    # Placeholder for other commands
    return {"message": "Je n'ai pas compris cette commande. Tape *menu* pour voir les options."}
