
import os
from PIL import Image
import requests
from io import BytesIO

class AIHandler:
    def __init__(self):
        # Ici on utiliserait l'API Gemini ou DALL-E pour les images
        self.api_key = os.getenv("GEMINI_API_KEY")

    def generate_image_from_text(self, prompt):
        """Simule la génération d'une image via IA."""
        print(f"🎨 Génération d'image pour : {prompt}")
        # Logique d'appel API GenAI ici
        return {"status": "success", "url": "https://images.remote.com/generated_id.png"}

    def create_sticker_from_image(self, image_url_or_path, is_from_net=True):
        """Transforme une image en sticker WhatsApp (WebP 512x512)."""
        try:
            if is_from_net:
                response = requests.get(image_url_or_path)
                img = Image.open(BytesIO(response.content))
            else:
                img = Image.open(image_url_or_path)

            # Redimensionnement au format sticker WhatsApp
            img.thumbnail((512, 512))
            
            # Création d'un fond transparent si nécessaire
            sticker_path = f"downloads/sticker_{os.urandom(4).hex()}.webp"
            img.save(sticker_path, "WEBP")
            
            return {"status": "success", "path": sticker_path}
        except Exception as e:
            return {"status": "error", "message": str(e)}

