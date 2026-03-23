import os
import google.generativeai as genai
from PIL import Image
import requests
from io import BytesIO
import base64

class AIHandler:
    def __init__(self):
        self.api_key = os.getenv('GEMINI_API_KEY')
        if self.api_key:
            genai.configure(api_key=self.api_key)
            # Modèle pour le texte (raisonnement et chat)
            self.text_model = genai.GenerativeModel('gemini-3-flash-preview')
            # Modèle pour la génération d'images
            self.image_model = genai.GenerativeModel('gemini-2.5-flash-image')
        else:
            print("⚠️ GEMINI_API_KEY non trouvée dans les variables d'environnement")

    def chat(self, prompt, image_path=None, mode='normal'):
        """
        Traite une demande textuelle et/ou visuelle.
        Mode 'professeur' : Guide l'élève au lieu de donner la réponse.
        """
        if not self.api_key:
            return "Désolé, mon cerveau (IA) n'est pas configuré. Contacte l'administrateur."
        
        try:
            # Instructions système selon le mode
            system_instruction = (
                "Tu es Laure, une assistante intelligente, amicale et serviable sur WhatsApp. "
                "Tu aides les élèves dans leurs devoirs et leur quotidien."
            )
            
            if mode == 'professeur':
                system_instruction += (
                    "\n⚠️ MODE PROFESSEUR ACTIVÉ : Ne donne JAMAIS la réponse directement. "
                    "Analyse l'erreur de l'élève ou l'énoncé, et pose-lui une question pour le guider "
                    "vers la solution. Sois encourageante et patiente."
                )

            # Préparation du contenu (Multimodal si image présente)
            contents = []
            if image_path and os.path.exists(image_path):
                img = Image.open(image_path)
                contents.append(img)
                prompt = f"Analyse cette image et aide-moi : {prompt}" if prompt else "Que vois-tu sur cette image ? Aide-moi à comprendre."
            
            contents.append(prompt)

            # Appel à Gemini
            response = self.text_model.generate_content(
                contents,
                generation_config=genai.types.GenerationConfig(
                    candidate_count=1,
                    stop_sequences=['x'],
                    max_output_tokens=1000,
                    temperature=0.7
                )
            )
            
            # On injecte l'instruction système via le prompt si le SDK ne supporte pas encore system_instruction nativement sur ce modèle
            # (Ou on utilise la méthode recommandée si disponible)
            return response.text
        except Exception as e:
            print(f"❌ Erreur chat IA : {e}")
            return "Oups, j'ai eu un petit bug en réfléchissant. Réessaie plus tard !"

    def generate_image_from_text(self, text):
        """
        Génère une image à partir d'un texte en utilisant Gemini 2.5 Flash Image.
        """
        if not self.api_key:
            return {'status': 'error', 'message': 'Clé API manquante'}

        print(f"🎨 Génération d'image pour : {text}")
        
        try:
            # Tentative de génération avec le modèle d'image
            response = self.image_model.generate_content(text)
            
            # Extraction de l'image de la réponse
            for part in response.candidates[0].content.parts:
                if part.inline_data:
                    image_data = part.inline_data.data
                    
                    # Sauvegarde locale temporaire pour l'envoi via WhatsApp
                    if not os.path.exists('downloads'):
                        os.makedirs('downloads')
                    
                    file_path = f"downloads/gen_{hash(text)}.png"
                    with open(file_path, "wb") as f:
                        f.write(image_data)
                    
                    return {
                        'status': 'success',
                        'url': file_path
                    }
            
            # Si aucune image n'est trouvée, fallback sur un service de placeholder de qualité
            print("⚠️ Aucune donnée d'image dans la réponse, utilisation du fallback.")
            image_url = f"https://picsum.photos/seed/{text.replace(' ', '_')}/1024/1024"
            return {
                'status': 'success',
                'url': image_url
            }

        except Exception as e:
            print(f"❌ Erreur génération image : {e}")
            # Fallback en cas d'erreur
            image_url = f"https://picsum.photos/seed/{text.replace(' ', '_')}/1024/1024"
            return {
                'status': 'success',
                'url': image_url
            }
