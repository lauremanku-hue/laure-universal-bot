import os
import requests
from io import BytesIO
import google.generativeai as genai
from google.generativeai import client

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
        self.model = None
        
        if self.api_key:
            try:
                # On force l'utilisation de la version 'v1' au lieu de 'v1beta'
                genai.configure(api_key=self.api_key, transport='rest') 
                
                # On définit le modèle explicitement
                model_name = 'gemini-1.5-flash'
                
                self.model = genai.GenerativeModel(
                    model_name=model_name
                )
                print(f"✅ Modèle {model_name} configuré sur API v1.")

    def generate_text(self, prompt):
        """Génère une réponse via Gemini avec gestion d'erreurs."""
        if not self.model:
            return "Désolé, mon cerveau (IA) n'est pas encore connecté. Contactez Laure !"
        
        # Sécurité souple pour éviter les blocages sur des questions d'examen
        safety_settings = [
            {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
            {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
            {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"},
            {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"},
        ]

        try:
            # Nettoyage et envoi
            safe_prompt = str(prompt).strip()
            response = self.model.generate_content(
                safe_prompt,
                safety_settings=safety_settings
            )
            
            if response and response.text:
                return response.text
            
            return "Je n'ai pas pu générer de réponse. Peux-tu reformuler ?"

        except Exception as e:
            error_msg = str(e)
            print(f"❌ Erreur Gemini : {error_msg}")
            
            if "quota" in error_msg.lower() or "429" in error_msg:
                return "⏳ Je suis un peu fatigué (limite atteinte). Réessaie dans une minute !"
            
            return "Oups, j'ai eu un petit bug. Réessaie une commande comme /cours ou /prix !"

    def generate_image_from_text(self, prompt):
        """Génère une image via Pollinations (Gratuit et rapide)."""
        print(f"🎨 Génération d'image : {prompt}")
        encoded_prompt = prompt.replace(' ', '%20')
        image_url = f"https://image.pollinations.ai/prompt/{encoded_prompt}?width=1024&height=1024&nologo=true"
        return {"status": "success", "url": image_url}

    def create_sticker_from_image(self, image_url_or_path, is_from_net=True):
        """Transforme une image en sticker WebP (nécessite Pillow)."""
        if not HAS_PILLOW:
            return {"status": "error", "message": "Module Pillow manquant sur Railway."}

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
