import os
import requests
from io import BytesIO
import google.generativeai as genai

# Import sécurisé de Pillow (PIL) pour les stickers/images
try:
    from PIL import Image
    HAS_PILLOW = True
except ImportError:
    HAS_PILLOW = False
    print("⚠️ AVERTISSEMENT : La librairie 'Pillow' n'est pas installée.")

class AIHandler:
    def __init__(self):
        """Initialise l'IA avec le modèle le plus récent et stable."""
        self.api_key = os.getenv("GEMINI_API_KEY")
        self.model = None
        
        if self.api_key:
            try:
                # Configuration de base
                genai.configure(api_key=self.api_key)
                
                # Utilisation de gemini-1.5-flash : rapide, gratuit et supporté en v1
                # On définit une instruction système pour donner une personnalité au bot
                system_instruction = (
                    "Tu es l'assistant de Laure. Tu aides les étudiants au Cameroun. "
                    "Sois amical, utilise parfois des expressions locales si besoin. "
                    "Tarifs : 500 FCFA (1 sem), 750 FCFA (2.5 sem), 1500 FCFA (1 mois). "
                    "Si on te demande un cours, donne un contenu structuré et éducatif."
                )

                self.model = genai.GenerativeModel(
                    model_name='gemini-1.5-flash',
                    system_instruction=system_instruction
                )
                print("✅ IA Gemini (1.5-flash) opérationnelle sur Railway.")
                
            except Exception as e:
                print(f"❌ Erreur critique configuration Gemini : {e}")
        else:
            print("⚠️ GEMINI_API_KEY manquante dans les variables d'environnement.")

    def generate_text(self, prompt):
        """Génère une réponse textuelle."""
        if not self.model:
            return "Désolé, mon cerveau est déconnecté. Contacte Laure !"
        
        # Paramètres pour éviter que l'IA ne bloque sur des sujets sensibles d'étudiants
        safety_settings = [
            {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
            {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
            {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"},
            {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"},
        ]

        try:
            response = self.model.generate_content(
                str(prompt),
                safety_settings=safety_settings
            )
            
            if response and response.text:
                return response.text
            
            return "Je n'ai pas pu générer de réponse. Réessaie avec une autre question."

        except Exception as e:
            error_msg = str(e)
            print(f"❌ Erreur lors de la génération : {error_msg}")
            
            if "429" in error_msg or "quota" in error_msg.lower():
                return "⏳ Trop de messages ! Attends une minute avant de me relancer."
            
            return "Oups, j'ai eu un petit bug. Réessaie une commande comme /cours ou /quiz !"

    def generate_image_from_text(self, prompt):
        """Génère une image via Pollinations (service externe gratuit)."""
        print(f"🎨 Requête image : {prompt}")
        encoded_prompt = prompt.replace(' ', '%20')
        # Ce service est parfait car il ne nécessite pas de clé API supplémentaire
        image_url = f"https://image.pollinations.ai/prompt/{encoded_prompt}?width=1024&height=1024&nologo=true"
        return {"status": "success", "url": image_url}

    def create_sticker_from_image(self, image_url_or_path, is_from_net=True):
        """Transforme une image en sticker .webp pour WhatsApp."""
        if not HAS_PILLOW:
            return {"status": "error", "message": "Pillow non installé sur le serveur."}

        try:
            if is_from_net:
                response = requests.get(image_url_or_path, timeout=10)
                img = Image.open(BytesIO(response.content))
            else:
                img = Image.open(image_url_or_path)

            # Format sticker WhatsApp : 512x512
            img.thumbnail((512, 512))
            
            output_dir = "downloads"
            if not os.path.exists(output_dir):
                os.makedirs(output_dir)
                
            sticker_path = os.path.join(output_dir, f"sticker_{os.urandom(3).hex()}.webp")
            img.save(sticker_path, "WEBP")
            
            return {"status": "success", "path": sticker_path}
        except Exception as e:
            print(f"❌ Erreur Sticker : {e}")
            return {"status": "error", "message": str(e)}
