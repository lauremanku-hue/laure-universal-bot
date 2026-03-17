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
                
                # Débogage : Lister les modèles disponibles pour voir ce qui est autorisé
                print("🔍 Vérification des modèles disponibles...")
                available_models = []
                try:
                    for m in genai.list_models():
                        if 'generateContent' in m.supported_generation_methods:
                            available_models.append(m.name)
                    print(f"📋 Modèles autorisés : {available_models}")
                except Exception as e:
                    print(f"⚠️ Impossible de lister les modèles : {e}")

                # Liste de modèles à essayer par ordre de préférence
                # On utilise les noms complets avec 'models/' car le SDK semble pointilleux
                model_candidates = [
                    'models/gemini-1.5-flash',
                    'models/gemini-1.5-flash-8b',
                    'models/gemini-1.0-pro',
                    'gemini-1.5-flash',
                    'gemini-pro'
                ]
                
                self.model = None
                for model_name in model_candidates:
                    try:
                        print(f"🔄 Tentative de configuration avec : {model_name}")
                        test_model = genai.GenerativeModel(model_name=model_name)
                        # Test rapide pour vérifier si le modèle répond (optionnel mais plus sûr)
                        self.model = test_model
                        self.model_name_used = model_name
                        print(f"✅ Modèle {model_name} sélectionné.")
                        break
                    except:
                        continue
                
                if not self.model:
                    print("❌ Aucun modèle Gemini n'a pu être configuré.")
            except Exception as e:
                self.model = None
                print(f"❌ Erreur configuration Gemini : {e}")
        else:
            self.model = None
            print("⚠️ GEMINI_API_KEY non configurée.")

    def generate_text(self, prompt):
        """Génère une réponse textuelle via Gemini avec une résilience maximale."""
        if not self.model:
            return "Désolé, mon cerveau (IA) n'est pas encore connecté. Contactez l'admin !"
        
        # Paramètres de sécurité très souples pour éviter les blocages
        safety_settings = [
            {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
            {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
            {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"},
            {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"},
        ]

        try:
            # Nettoyage du prompt
            safe_prompt = str(prompt).encode('utf-8', 'ignore').decode('utf-8')
            
            # Tentative de génération standard (plus rapide et stable)
            response = self.model.generate_content(
                safe_prompt,
                safety_settings=safety_settings
            )
            
            if response and hasattr(response, 'text') and response.text:
                return response.text
            
            # Gestion des cas où la réponse est bloquée ou vide
            if response and hasattr(response, 'candidates') and response.candidates:
                candidate = response.candidates[0]
                if hasattr(candidate.content, 'parts'):
                    text_parts = [p.text for p in candidate.content.parts if hasattr(p, 'text')]
                    if text_parts:
                        return "".join(text_parts)
            
            return "Je n'ai pas pu formuler de réponse claire. Peux-tu reformuler ta question ?"

        except Exception as e:
            error_msg = str(e)
            print(f"❌ Erreur Gemini Text : {error_msg}")
            
            if "quota" in error_msg.lower() or "429" in error_msg:
                return "⏳ Je suis un peu fatiguée (quota atteint). Réessaie dans une minute !"
            
            if "api_key" in error_msg.lower() or "403" in error_msg:
                return "⚠️ Erreur de configuration : La clé API est invalide ou restreinte."

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
