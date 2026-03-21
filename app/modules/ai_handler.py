import os
import requests
from io import BytesIO
from google import genai
from google.genai import types

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
        self.client = None
        self.model_name_used = "aucun"
        
        if self.api_key:
            try:
                # Configuration avec le nouveau SDK
                self.client = genai.Client(api_key=self.api_key)
                
                print("🔍 Recherche des modèles Gemini accessibles...")
                try:
                    models = [m.name for m in self.client.models.list()]
                    print(f"📋 Modèles trouvés : {models}")
                except Exception as e:
                    print(f"⚠️ Erreur lors du listage des modèles : {e}")
                    models = []

                # Liste de priorité intelligente (modèles stables d'abord)
                candidates = [
                    'gemini-2.0-flash-lite-preview-09-2025',
                    'gemini-2.0-flash-lite',
                    'gemini-flash-latest',
                    'gemini-pro-latest',
                    'gemini-1.5-flash',
                    'gemini-2.0-flash',
                    'gemini-1.5-pro',
                    'gemma-3-27b-it',
                    'gemma-3-12b-it',
                    'gemma-3-4b-it',
                    'gemma-3-1b-it'
                ]
                
                import time
                for model_name in candidates:
                    try:
                        print(f"🔄 Validation IA : {model_name}")
                        # Test de validation minimal
                        self.client.models.generate_content(
                            model=model_name,
                            contents="test",
                            config=types.GenerateContentConfig(max_output_tokens=1)
                        )
                        self.model_name_used = model_name
                        print(f"✅ IA opérationnelle avec : {model_name}")
                        break
                    except Exception as e:
                        err_msg = str(e).lower()
                        print(f"❌ {model_name} indisponible : {err_msg[:50]}")
                        if "429" in err_msg or "quota" in err_msg:
                            print("⏳ Quota atteint, petite pause avant le prochain modèle...")
                            time.sleep(2) # Pause pour laisser le quota respirer
                        self.model_name_used = "aucun"
                
                if self.model_name_used == "aucun":
                    print("⚠️ Aucun modèle n'a pu être validé. Laure fonctionnera en mode dégradé.")
            except Exception as e:
                print(f"❌ Erreur critique configuration IA : {e}")
        else:
            print("⚠️ GEMINI_API_KEY manquante dans l'environnement.")

    def generate_text(self, prompt, retries=2):
        """Génère une réponse textuelle avec une tolérance aux pannes maximale."""
        if not self.client or self.model_name_used == "aucun":
            return "Désolé, mon cerveau (IA) n'est pas encore configuré. Vérifiez la clé API !"
        
        # Paramètres de sécurité
        safety_settings = [
            types.SafetySetting(category="HARM_CATEGORY_HARASSMENT", threshold="BLOCK_NONE"),
            types.SafetySetting(category="HARM_CATEGORY_HATE_SPEECH", threshold="BLOCK_NONE"),
            types.SafetySetting(category="HARM_CATEGORY_SEXUALLY_EXPLICIT", threshold="BLOCK_NONE"),
            types.SafetySetting(category="HARM_CATEGORY_DANGEROUS_CONTENT", threshold="BLOCK_NONE"),
        ]

        try:
            # Nettoyage et préparation
            safe_prompt = str(prompt).strip()
            
            # Appel API avec le nouveau SDK
            response = self.client.models.generate_content(
                model=self.model_name_used,
                contents=safe_prompt,
                config=types.GenerateContentConfig(
                    safety_settings=safety_settings
                )
            )
            
            # Extraction sécurisée du texte
            if response and response.text:
                return response.text
            
            return "Je n'ai pas réussi à formuler une réponse. Peux-tu me poser la question autrement ?"

        except Exception as e:
            error_msg = str(e).lower()
            print(f"❌ Erreur génération texte ({self.model_name_used}) : {error_msg}")
            
            if ("500" in error_msg or "internal error" in error_msg) and retries > 0:
                print(f"🔄 Erreur 500 détectée, tentative de retry ({retries} restantes)...")
                import time
                time.sleep(1)
                return self.generate_text(prompt, retries=retries-1)

            if "quota" in error_msg or "429" in error_msg:
                return "⏳ Je suis un peu surchargée (quota atteint). Réessaie dans une minute !"
            
            if "safety" in error_msg or "finish_reason: 3" in error_msg:
                return "🛡️ Désolé, ce sujet est bloqué par mes filtres de sécurité. Essayons autre chose !"

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
