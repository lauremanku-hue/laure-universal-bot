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

    def send_local_file(self, chat_id, file_path, media_type):
        """Envoie un fichier local vers Telegram."""
        if not self.token: return False
        method = 'sendAudio' if media_type == 'audio' else 'sendVideo'
        url = f"{self.base_url}/{method}"
        files = {
            'audio' if media_type == 'audio' else 'video': open(file_path, 'rb')
        }
        data = {'chat_id': chat_id}
        try:
            response = requests.post(url, data=data, files=files)
            return response.json()
        except Exception as e:
            print(f"❌ Erreur Telegram send_local_file: {e}")
            return False

    def set_bot_commands(self):
        """Configure le menu des commandes du bot Telegram."""
        if not self.token: return False
        url = f"{self.base_url}/setMyCommands"
        commands = [
            {"command": "start", "description": "Lancer le bot et voir le menu"},
            {"command": "menu", "description": "Menu"},
            {"command": "img", "description": "image"},
            {"command": "audio", "description": "audio"},
            {"command": "video", "description": "Vidéo"},
            {"command": "cours", "description": "Suivre un cours interactif"},
            {"command": "quiz", "description": "Quiz"},
            {"command": "quiz_result", "description": "résultats quiz"},
            {"command": "profil", "description": "Statut et bonus"},
            {"command": "pay", "description": "VIP"},
            {"command": "blague", "description": "Blague"},
            {"command": "de", "description": "Lancer un dé"},
            {"command": "terre", "description": "Un fait sur la Terre"},
            {"command": "tagall", "description": "Taguer le monde (Groupes)"},
            {"command": "checkwa", "description": "Vérifier numéro WhatsApp"},
            {"command": "restore", "description": "Restaurer un message supprimé"}
        ]
        try:
            return requests.post(url, json={"commands": commands}).json()
        except Exception as e:
            print(f"❌ Erreur Telegram set_bot_commands: {e}")
            return False
