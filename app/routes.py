from flask import Blueprint, jsonify, request, render_template_string
from .models import User, MessageLog
from .extensions import db
import os
from .modules.whatsapp_web import bot 

main = Blueprint('main', __name__)

@main.route('/')
def index():
    # We'll try to get the bot instance from the current_app if we can find it
    # But for now, let's just show a status page
    return render_template_string("""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Laure Bot Status</title>
        <style>
            body { font-family: sans-serif; text-align: center; padding: 50px; background: #f4f4f9; }
            .card { background: white; padding: 30px; border-radius: 10px; box-shadow: 0 4px 6px rgba(0,0,0,0.1); display: inline-block; }
            h1 { color: #25d366; }
            .status { font-weight: bold; color: #555; }
            .qr-placeholder { margin: 20px; border: 2px dashed #ccc; padding: 20px; color: #888; }
        </style>
    </head>
    <body>
        <div class="card">
            <h1>🌟 Laure Bot</h1>
            <p class="status">Statut : <span style="color: green;">En ligne</span></p>
            <p>Le bot WhatsApp est en cours d'exécution.</p>
            <div class="qr-placeholder">
                <p>Si vous n'êtes pas encore connecté, consultez les logs pour le QR code ou le code de couplage.</p>
            </div>
            <hr>
            <p><small>Propulsé par Neonize & Gemini AI</small></p>
        </div>
    </body>
    </html>
    """)

def process_command(user, msg, platform):
    """
    Process a command from a user and return a response.
    """
    clean_msg = msg.lower().strip()
    
    if clean_msg == 'menu':
        return {
            "message": (
                "🌟 *MENU DE LAURE* 🌟\n\n"
                "Voici ce que je peux faire pour toi :\n"
                "1. 🎨 *Générer une image* : Tape `/img <ta description>`\n"
                "2. 🎵 *Télécharger de l'audio* : Tape `/audio <ta recherche>`\n"
                "3. 🎥 *Télécharger de la vidéo* : Tape `/video <ta recherche>`\n"
                "4. 📚 *Cours et Quiz* : Tape `quiz` pour commencer un quiz\n"
                "5. 💰 *Mon Solde* : Tape `/solde` pour voir tes crédits\n"
                "6. 💎 *Accès VIP* : Tape `vip` pour voir les offres"
            )
        }
    
    if clean_msg == '/solde':
        return {
            "message": f"💰 *TON SOLDE* : {user.balance} FCFA\n\n"
                       f"Statut VIP : {'✅ ACTIF' if user.is_premium else '❌ INACTIF'}"
        }
    
    if clean_msg == 'vip':
        return {
            "message": (
                "💎 *OFFRES VIP LAURE* 💎\n\n"
                "Deviens VIP pour profiter de :\n"
                "- 🎨 Images IA illimitées\n"
                "- 🎵 Téléchargements Audio/Vidéo illimités\n"
                "- 📚 Accès complet aux cours et quiz\n"
                "- 🚀 Réponses prioritaires\n\n"
                "Options :\n"
                "1. *Journée* : 200 FCFA\n"
                "2. *Semaine* : 1000 FCFA\n"
                "3. *Mois* : 3000 FCFA\n\n"
                "Pour t'abonner, contacte l'administrateur ou tape `payer`."
            )
        }
    
    if clean_msg == 'payer':
        return {
            "message": (
                "💳 *PAIEMENT LAURE* 💳\n\n"
                "Pour recharger ton compte ou devenir VIP, utilise l'un des moyens suivants :\n\n"
                "🟠 *Orange Money* : #144# (Numéro : 07XXXXXXXX)\n"
                "🟡 *MTN Mobile Money* : *133# (Numéro : 05XXXXXXXX)\n"
                "🔵 *Wave* : Utilise l'application (Numéro : 01XXXXXXXX)\n\n"
                "⚠️ *IMPORTANT* : Envoie une capture d'écran du reçu à l'administrateur pour validation."
            )
        }
    
    # Placeholder for other commands
    return {"message": "Je n'ai pas compris cette commande. Tape *menu* pour voir les options."}
