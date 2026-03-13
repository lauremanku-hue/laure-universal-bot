
import os
import requests
from io import BytesIO
import google.generativeai as genai

# Import sécurisé de Pillow (PIL)
try:
    from PIL import Image
    HAS_PILLOW = True
except ImportError:
    HAS_PILLOW = False
    print("⚠️ AVERTISSEMENT : La librairie 'Pillow' n'est pas installée.")

class AIHandler:
    def __init__(self):
        self.api_key = os.getenv("GEMINI_API_KEY")
        if self.api_key:
            try:
                genai.configure(api_key=self.api_key)
                # Utilisation d'un modèle plus récent et stable
                self.model = genai.GenerativeModel('gemini-1.5-flash-latest')
                print("✅ Gemini configuré avec succès.")
            except Exception as e:
                self.model = None
                print(f"❌ Erreur configuration Gemini : {e}")
        else:
            self.model = None
            print("⚠️ GEMINI_API_KEY non configurée.")

    def generate_text(self, prompt):
        """Génère une réponse textuelle via Gemini."""
        if not self.model:
            return "Désolé, mon cerveau (IA) n'est pas encore connecté. Contactez l'admin !"
        
        try:
            # Ajout d'un timeout ou d'une gestion plus fine si nécessaire
            response = self.model.generate_content(prompt)
            if response and response.text:
                return response.text
            else:
                return "Je n'ai pas pu formuler de réponse. Réessaie avec une autre question !"
        except Exception as e:
            error_msg = str(e)
            print(f"❌ Erreur Gemini Text : {error_msg}")
            if "API_KEY_INVALID" in error_msg:
                return "⚠️ Erreur technique : La clé API de l'IA est invalide. Contactez l'admin."
            elif "quota" in error_msg.lower():
                return "⏳ Je suis un peu fatiguée (quota atteint). Réessaie dans quelques minutes !"
            return "Oups, j'ai eu un petit bug en réfléchissant. Réessaie plus tard !"

    def generate_image_from_text(self, prompt):
        """Simule la génération d'une image via IA."""
        print(f"🎨 Requête d'image : {prompt}")
        return {"status": "success", "url": f"https://picsum.photos/seed/{prompt.replace(' ', '_')}/512/512"}

    def create_sticker_from_image(self, image_url_or_path, is_from_net=True):
        if not HAS_PILLOW:
            return {"status": "error", "message": "Module Pillow non installé."}

        try:
            if is_from_net:
                response = requests.get(image_url_or_path, timeout=10)
                img = Image.open(BytesIO(response.content))
            else:
                img = Image.open(image_url_or_path)

            img.thumbnail((512, 512))
            output_dir = "downloads"
            if not os.path.exists(output_dir):
                os.makedirs(output_dir)
                
            sticker_path = os.path.join(output_dir, f"sticker_{os.urandom(4).hex()}.webp")
            img.save(sticker_path, "WEBP")
            
            return {"status": "success", "path": sticker_path}
        except Exception as e:
            return {"status": "error", "message": str(e)}
