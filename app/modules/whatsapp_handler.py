import os
import requests
import mimetypes

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

        # WhatsApp limit is 4096 characters.
        # If text is longer, we split it.
        MAX_LEN = 4000 # Safety margin
        if len(text) > MAX_LEN:
            parts = [text[i:i+MAX_LEN] for i in range(0, len(text), MAX_LEN)]
            results = []
            for part in parts:
                res = self._send_single_text(recipient_id, part)
                results.append(res)
            return results[0] if results else {"error": "No parts sent"}
        
        return self._send_single_text(recipient_id, text)

    def _send_single_text(self, recipient_id, text):
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
        
        # Détecter le type MIME réel du fichier
        mime_type, _ = mimetypes.guess_type(file_path)
        
        # Correction pour Meta : m4a doit être audio/mp4 ou audio/aac
        if file_path.endswith('.m4a'):
            mime_type = "audio/mp4"
        elif not mime_type:
            mime_type = "audio/mpeg" if media_type == "audio" else "video/mp4"
            
        print(f"📤 Upload WhatsApp: {file_path} (MIME: {mime_type}, Type: {media_type})")
        
        files = {
            "file": (os.path.basename(file_path), open(file_path, "rb"), mime_type),
            "messaging_product": (None, "whatsapp"),
            "type": (None, media_type)
        }
        try:
            response = requests.post(url, headers=headers, files=files)
            res_json = response.json()
            if "id" not in res_json:
                print(f"❌ Erreur upload WhatsApp: {res_json}")
                return {"error": res_json}
            return res_json.get("id")
        except Exception as e:
            print(f"❌ Erreur upload WhatsApp: {e}")
            return {"error": str(e)}

    def send_local_media(self, recipient_id, file_path, media_type):
        """Upload et envoie un média local."""
        res_upload = self.upload_media(file_path, media_type)
        if isinstance(res_upload, dict) and "error" in res_upload:
            return res_upload
        
        media_id = res_upload
        if not media_id: return {"error": "Upload failed (no id)"}

        print(f"🚀 Envoi média WhatsApp: {media_id} à {recipient_id}")
        
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
        try:
            response = requests.post(self.url, headers=headers, json=payload)
            res_json = response.json()
            print(f"📩 Réponse envoi WhatsApp: {res_json}")
            return res_json
        except Exception as e:
            print(f"❌ Erreur envoi WhatsApp: {e}")
            return {"error": str(e)}
