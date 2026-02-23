import requests
import smtplib
from email.mime.text import MIMEText
import os

# --- CONFIGURATION ---
# Meta (WhatsApp, Messenger, Instagram)
META_TOKEN = os.environ.get("META_TOKEN")
WA_PHONE_ID = os.environ.get("WHATSAPP_PHONE_ID")
FB_PAGE_ID = os.environ.get("FB_PAGE_ID")

# Telegram
TG_TOKEN = os.environ.get("TELEGRAM_TOKEN")

# Email (Gmail)
EMAIL_USER = os.environ.get("EMAIL_USER")
EMAIL_PASS = os.environ.get("EMAIL_PASS") # Mot de passe d'application Google

def send_whatsapp(to_number, text):
    """Envoie sur WhatsApp."""
    if not META_TOKEN: return print(f"⚠️ [Simul WA] À {to_number} : {text}")
    
    url = f"https://graph.facebook.com/v17.0/{WA_PHONE_ID}/messages"
    headers = {"Authorization": f"Bearer {META_TOKEN}", "Content-Type": "application/json"}
    payload = {"messaging_product": "whatsapp", "to": to_number, "type": "text", "text": {"body": text}}
    requests.post(url, json=payload, headers=headers)

def send_messenger(user_id, text):
    """Envoie sur Facebook Messenger."""
    if not META_TOKEN: return print(f"⚠️ [Simul Messenger] À {user_id} : {text}")

    url = f"https://graph.facebook.com/v17.0/me/messages?access_token={META_TOKEN}"
    payload = {"recipient": {"id": user_id}, "message": {"text": text}}
    requests.post(url, json=payload)

def send_instagram(user_id, text):
    """Envoie sur Instagram Direct (DM)."""
    if not META_TOKEN: return print(f"⚠️ [Simul Insta] À {user_id} : {text}")

    # L'API Instagram est très similaire à Messenger
    url = f"https://graph.facebook.com/v17.0/me/messages?access_token={META_TOKEN}"
    payload = {"recipient": {"id": user_id}, "message": {"text": text}}
    requests.post(url, json=payload)

def send_telegram(chat_id, text):
    """Envoie sur Telegram."""
    if not TG_TOKEN: return print(f"⚠️ [Simul Telegram] À {chat_id} : {text}")

    url = f"https://api.telegram.org/bot{TG_TOKEN}/sendMessage"
    payload = {"chat_id": chat_id, "text": text}
    requests.post(url, json=payload)

def send_email(to_email, subject, body):
    """Envoie un Email via Gmail (SMTP)."""
    if not EMAIL_USER: return print(f"⚠️ [Simul Email] À {to_email} : {subject} - {body}")

    msg = MIMEText(body)
    msg['Subject'] = subject
    msg['From'] = EMAIL_USER
    msg['To'] = to_email

    try:
        # Connexion au serveur Gmail
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
            server.login(EMAIL_USER, EMAIL_PASS)
            server.send_message(msg)
    except Exception as e:
        print(f"Erreur Email: {e}")

def send_youtube_comment(comment_id, text):
    """Répond à un commentaire YouTube (Placeholder)."""
    print(f"⚠️ [Simul YouTube] Réponse au com {comment_id} : {text}")
    # Nécessite l'API Google YouTube Data v3
