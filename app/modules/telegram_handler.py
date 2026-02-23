import os
import requests

class TelegramHandler:
    def __init__(self):
        self.token = os.getenv("TELEGRAM_TOKEN")
        self.base_url = f"https://api.telegram.org/bot{self.token}"

    def send_message(self, chat_id, text):
        url = f"{self.base_url}/sendMessage"
        payload = {"chat_id": chat_id, "text": text, "parse_mode": "Markdown"}
        return requests.post(url, json=payload).json()

    def send_photo(self, chat_id, photo_url, caption=""):
        url = f"{self.base_url}/sendPhoto"
        payload = {"chat_id": chat_id, "photo": photo_url, "caption": caption}
        return requests.post(url, json=payload).json()

    def send_sticker(self, chat_id, sticker_path):
        url = f"{self.base_url}/sendSticker"
        with open(sticker_path, 'rb') as sticker:
            files = {'sticker': sticker}
            data = {'chat_id': chat_id}
            return requests.post(url, data=data, files=files).json()
