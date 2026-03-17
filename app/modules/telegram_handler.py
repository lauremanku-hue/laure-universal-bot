import os
import requests

class TelegramHandler:
    def __init__(self):
        self.token = os.getenv("TELEGRAM_BOT_TOKEN")
        self.base_url = f"https://api.telegram.org/bot{self.token}"

    def send_message(self, chat_id, text):
        """Envoie un message texte sur Telegram."""
        if not self.token:
            print("⚠️ TelegramHandler: Token manquant")
            return False
            
        url = f"{self.base_url}/sendMessage"
        payload = {
            "chat_id": chat_id,
            "text": text,
            "parse_mode": "Markdown"
        }
        try:
            response = requests.post(url, json=payload)
            return response.json()
        except Exception as e:
            print(f"❌ Erreur Telegram send_message: {e}")
            return False

    def send_photo(self, chat_id, photo_url, caption=None):
        """Envoie une photo via une URL publique sur Telegram."""
        if not self.token: return False
        url = f"{self.base_url}/sendPhoto"
        payload = {
            "chat_id": chat_id,
            "photo": photo_url,
            "caption": caption,
            "parse_mode": "Markdown"
        }
        try:
            return requests.post(url, json=payload).json()
        except Exception as e:
            print(f"❌ Erreur Telegram send_photo: {e}")
            return False
