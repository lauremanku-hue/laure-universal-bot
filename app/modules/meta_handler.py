import os
import requests

class MetaHandler:
    def __init__(self):
        # Ce token sera à ajouter dans tes variables Railway (FB_INSTAGRAM_TOKEN)
        self.access_token = os.getenv("FB_INSTAGRAM_TOKEN")
        self.version = "v18.0"
        self.url = f"https://graph.facebook.com/{self.version}/me/messages"

    def send_message(self, recipient_id, text, platform='messenger'):
        """Envoie un message sur Messenger ou Instagram."""
        if not self.access_token:
            print(f"⚠️ MetaHandler ({platform}): Token manquant dans les variables d'environnement")
            return {"error": "Token manquant"}

        headers = {
            "Content-Type": "application/json",
        }
        params = {
            "access_token": self.access_token
        }
        payload = {
            "recipient": {"id": recipient_id},
            "message": {"text": text}
        }
        
        try:
            response = requests.post(self.url, headers=headers, params=params, json=payload)
            return response.json()
        except Exception as e:
            print(f"❌ Erreur MetaHandler ({platform}): {e}")
            return {"error": str(e)}
