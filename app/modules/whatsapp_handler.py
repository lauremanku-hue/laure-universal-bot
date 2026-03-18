import os
import requests

class WhatsAppHandler:
    def __init__(self):
        self.access_token = os.getenv("WHATSAPP_TOKEN")
        self.phone_number_id = os.getenv("PHONE_NUMBER_ID") or os.getenv("WHATSAPP_PHONE_ID")
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

    def send_image(self, recipient_id, image_url, caption=None):
        """Envoie une image via une URL publique."""
        headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json",
        }
        payload = {
            "messaging_product": "whatsapp",
            "to": recipient_id,
            "type": "image",
            "image": {
                "link": image_url
            }
        }
        if caption:
            payload["image"]["caption"] = caption
            
        try:
            response = requests.post(self.url, headers=headers, json=payload)
            return response.json()
        except Exception as e:
            print(f"❌ Erreur WhatsApp send_image: {e}")
            return {"error": str(e)}

    def upload_media(self, file_path, media_type):
        """Upload un fichier local vers Meta et retourne le media_id."""
        url = f"https://graph.facebook.com/{self.version}/{self.phone_number_id}/media"
        headers = {
            "Authorization": f"Bearer {self.access_token}"
        }
        files = {
            "file": (os.path.basename(file_path), open(file_path, "rb"), "audio/mpeg" if media_type == "audio" else "video/mp4"),
            "messaging_product": (None, "whatsapp"),
            "type": (None, media_type)
        }
        try:
            response = requests.post(url, headers=headers, files=files)
            return response.json().get("id")
        except Exception as e:
            print(f"❌ Erreur upload WhatsApp: {e}")
            return None

    def send_local_media(self, recipient_id, file_path, media_type):
        """Upload et envoie un média local."""
        media_id = self.upload_media(file_path, media_type)
        if not media_id: return {"error": "Upload failed"}

        headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json",
        }
        payload = {
            "messaging_product": "whatsapp",
            "to": recipient_id,
            "type": media_type,
            media_type: {"id": media_id}
        }
        return requests.post(self.url, headers=headers, json=payload).json()
