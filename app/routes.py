import os
import json
import qrcode
import io
import base64
from flask import Blueprint, jsonify, request, render_template_string, current_app
from .models import User, MessageLog, QuizSession
from .extensions import db
from datetime import datetime, timedelta

main = Blueprint('main', __name__)

@main.route('/')
def index():
    bot = getattr(current_app, 'bot', None)
    qr_img_base64 = None
    pairing_code = getattr(bot, 'pairing_code', None) if bot else None
    
    if bot and bot.current_qr and not pairing_code:
        try:
            qr = qrcode.QRCode(version=1, box_size=10, border=5)
            qr.add_data(bot.current_qr)
            qr.make(fit=True)
            img = qr.make_image(fill_color="black", back_color="white")
            
            buffered = io.BytesIO()
            img.save(buffered, format="PNG")
            qr_img_base64 = base64.b64encode(buffered.getvalue()).decode()
        except Exception as e:
            print(f"⚠️ Erreur génération image QR : {e}")
    
    return render_template_string("""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Laure Bot Status</title>
        <style>
            body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; text-align: center; padding: 20px; background: #f0f2f5; color: #1c1e21; }
            .card { background: white; padding: 30px; border-radius: 15px; box-shadow: 0 8px 24px rgba(0,0,0,0.1); display: inline-block; max-width: 500px; width: 100%; }
            h1 { color: #25d366; margin-bottom: 10px; }
            .status { font-size: 1.1em; margin-bottom: 20px; }
            .qr-container { margin: 20px 0; padding: 15px; background: #fff; border: 1px solid #ddd; border-radius: 10px; }
            .qr-image { max-width: 100%; height: auto; }
            .pairing-box { background: #e7f3ff; padding: 20px; border-radius: 10px; margin: 20px 0; border: 2px solid #007bff; }
            .pairing-code { font-size: 2.5em; font-weight: bold; letter-spacing: 5px; color: #007bff; margin: 10px 0; }
            .instructions { text-align: left; background: #f8f9fa; padding: 15px; border-radius: 8px; font-size: 0.9em; margin-top: 20px; }
            .footer { margin-top: 20px; color: #65676b; font-size: 0.8em; }
            .btn { background: #25d366; color: white; padding: 10px 20px; border-radius: 5px; text-decoration: none; display: inline-block; margin-top: 10px; font-weight: bold; border: none; cursor: pointer; }
            .btn-blue { background: #007bff; }
            input { padding: 10px; border-radius: 5px; border: 1px solid #ccc; width: 70%; margin-bottom: 10px; }
        </style>
        {% if not pairing_code %}
        <meta http-equiv="refresh" content="15">
        {% endif %}
    </head>
    <body>
        <div class="card">
            <h1>🌟 Laure Bot</h1>
            <div class="status">
                {% if pairing_code %}
                    <span style="color: #007bff;">📲 Code de couplage généré</span>
                {% elif qr_img_base64 %}
                    <span style="color: #e4a11b;">⏳ En attente de connexion...</span>
                {% else %}
                    <span style="color: #25d366;">✅ Bot Connecté & Prêt</span>
                {% endif %}
            </div>
            
            {% if pairing_code %}
                <div class="pairing-box">
                    <p>Votre code de couplage :</p>
                    <div class="pairing-code">{{ pairing_code }}</div>
                    <p><small>Saisissez ce code sur votre téléphone.</small></p>
                </div>
            {% elif qr_img_base64 %}
                <div class="qr-container">
                    <img src="data:image/png;base64,{{ qr_img_base64 }}" class="qr-image" alt="WhatsApp QR Code">
                    <p><strong>Scannez le QR Code</strong></p>
                </div>
                
                <div style="margin: 20px 0; border-top: 1px solid #eee; padding-top: 20px;">
                    <p><strong>OU connectez-vous par numéro :</strong></p>
                    <form action="/pair" method="POST">
                        <input type="text" name="phone" placeholder="Ex: 237690000000" required>
                        <button type="submit" class="btn btn-blue">Recevoir un code</button>
                    </form>
                </div>
            {% else %}
                <div style="padding: 20px; color: #25d366;">
                    <p style="font-size: 3em;">🚀</p>
                    <p><strong>Laure est en ligne !</strong></p>
                </div>
            {% endif %}

            <div class="instructions">
                <strong>Comment utiliser le code ?</strong>
                <ol>
                    <li>Ouvrez WhatsApp > <strong>Appareils connectés</strong>.</li>
                    <li>Appuyez sur <strong>Connecter un appareil</strong>.</li>
                    <li>Appuyez sur <strong>"Connecter avec le numéro de téléphone"</strong> en bas.</li>
                    <li>Saisissez le code affiché ci-dessus.</li>
                </ol>
            </div>
            
            <a href="/" class="btn">Actualiser</a>
            
            <div class="footer">
                Propulsé par Neonize & Gemini AI | Laure Bot v1.1
            </div>
        </div>
    </body>
    </html>
    """, qr_img_base64=qr_img_base64, pairing_code=pairing_code)

@main.route('/pair', methods=['POST'])
def pair_with_phone():
    from flask import current_app, redirect, url_for, request, flash
    phone = request.form.get('phone')
    bot = getattr(current_app, 'bot', None)
    
    if bot and phone:
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
