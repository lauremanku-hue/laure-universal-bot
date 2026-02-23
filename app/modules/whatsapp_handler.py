import os
import requests

class WhatsAppHandler:
    def __init__(self):
        self.access_token = os.getenv("WHATSAPP_TOKEN")
        self.phone_number_id = os.getenv("PHONE_NUMBER_ID") # Match config.py
        self.version = "v18.0"
        self.url = f"https://graph.facebook.com/{self.version}/{self.phone_number_id}/messages"

    def send_text(self, recipient_id, text):
        """Envoie un message texte via l'API Meta."""
        if not self.access_token or not self.phone_number_id:
            print("⚠️ WhatsAppHandler: Token ou PhoneID manquant dans .env")
            return {"error": "Config manquante"}

        headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json",
        }
        payload = {
            "messaging_product": "whatsapp",
            "to": recipient_id,
            "type": "text",
            "text": {"body": text}
        }
        try:
            response = requests.post(self.url, headers=headers, json=payload)
            return response.json()
        except Exception as e:
            print(f"❌ Erreur send_text: {e}")
            return {"error": str(e)}

    def send_sticker(self, recipient_id, sticker_id):
        """Envoie un sticker par son ID média Meta."""
        headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json",
        }
        payload = {
            "messaging_product": "whatsapp",
            "to": recipient_id,
            "type": "sticker",
            "sticker": {"id": sticker_id}
        }
        return requests.post(self.url, headers=headers, json=payload).json()

