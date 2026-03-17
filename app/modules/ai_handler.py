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
                # Tentative avec grounding, sinon repli sur modèle standard
                try:
                    self.model = genai.GenerativeModel(
                        model_name='gemini-1.5-flash',
                        tools=[{'google_search_retrieval': {}}]
                    )
                    print("✅ Gemini 1.5 Flash configuré avec Grounding.")
                except:
                    self.model = genai.GenerativeModel(model_name='gemini-1.5-flash')
                    print("✅ Gemini 1.5 Flash configuré (Mode Standard).")
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
            # Nettoyage du prompt
            safe_prompt = str(prompt).encode('utf-8', 'ignore').decode('utf-8')
            response = self.model.generate_content(safe_prompt)
            
            if response and hasattr(response, 'text') and response.text:
                return response.text
            
            # Fallback si parts est présent mais pas text (grounding ou blocage)
            if response and hasattr(response, 'parts'):
                text_parts = [p.text for p in response.parts if hasattr(p, 'text')]
                if text_parts:
                    return "".join(text_parts)
            
            return "Je n'ai pas pu formuler de réponse claire. Peux-tu reformuler ?"
        except Exception as e:
            error_msg = str(e)
            print(f"❌ Erreur Gemini Text : {error_msg}")
            # Si l'erreur vient du grounding, on tente sans outils
            if "google_search_retrieval" in error_msg:
                try:
                    simple_model = genai.GenerativeModel(model_name='gemini-1.5-flash')
                    res = simple_model.generate_content(prompt)
                    return res.text
                except: pass
            
            if "quota" in error_msg.lower():
                return "⏳ Je suis un peu fatiguée (quota atteint). Réessaie dans quelques minutes !"
            return "Oups, j'ai eu un petit bug en réfléchissant. Réessaie plus tard !"

    def generate_image_from_text(self, prompt):
        """Génère une image via l'IA (Simulation améliorée ou API réelle si possible)."""
        print(f"🎨 Requête d'image : {prompt}")
        # En attendant une intégration Imagen complète, on utilise un service de génération plus performant
        # On utilise Pollinations.ai qui génère de vraies images correspondant au prompt
        encoded_prompt = prompt.replace(' ', '%20')
        image_url = f"https://image.pollinations.ai/prompt/{encoded_prompt}?width=1024&height=1024&nologo=true"
        return {"status": "success", "url": image_url}

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
