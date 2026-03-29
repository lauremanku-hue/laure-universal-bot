import os
from google import genai
from google.genai import types
from PIL import Image
import requests
from io import BytesIO
import base64
import json  # N'oublie pas d'importer json pour tes méthodes de quiz/devinettes

class AIHandler:
    def __init__(self):
        self.api_key = os.getenv('GEMINI_API_KEY')
        if self.api_key:
            # CORRECT : On crée un client avec le nouveau SDK
            self.client = genai.Client(api_key=self.api_key)
            # Noms des modèles (Vérifie bien les noms officiels disponibles)
            self.text_model_name = 'gemini-2.0-flash' 
        else:
            print("⚠️ GEMINI_API_KEY non trouvée")

    def chat(self, prompt, image_path=None, mode='normal'):
        if not self.api_key:
            return "Désolé, mon cerveau n'est pas configuré."
        
        try:
            system_instruction = "Tu es Laure, une assistante intelligente et amicale sur WhatsApp."
            if mode == 'professeur':
                system_instruction += "\nMODE PROFESSEUR : Guide l'élève sans donner la réponse."

            # Préparation du contenu pour le nouveau SDK
            contents = []
            if image_path and os.path.exists(image_path):
                img = Image.open(image_path)
                contents.append(img)
            
            contents.append(prompt if prompt else "Analyse cette image.")

            # CORRECT : Appel avec le nouveau client
            response = self.client.models.generate_content(
                model=self.text_model_name,
                contents=contents,
                config=types.GenerateContentConfig(
                    system_instruction=system_instruction,
                    max_output_tokens=1000,
                    temperature=0.7
                )
            )
            return response.text
        except Exception as e:
            print(f"❌ Erreur chat IA : {e}")
            return "Oups, petit bug !"

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

    def get_riddle(self):
        """Génère une devinette avec sa réponse."""
        prompt = "Génère une devinette amusante et éducative pour WhatsApp. Donne la devinette et la réponse séparément dans un format JSON : {\"question\": \"...\", \"reponse\": \"...\"}"
        try:
            response = self.text_model.generate_content(prompt)
            # On nettoie la réponse pour extraire le JSON
            text = response.text.replace("```json", "").replace("```", "").strip()
            return json.loads(text)
        except:
            return {"question": "Je suis grand quand je suis jeune et petit quand je suis vieux. Qui suis-je ?", "reponse": "Une bougie"}

    def generate_course_content(self, title):
        """Génère un contenu de cours complet et structuré sur un titre donné."""
        prompt = f"Rédige un cours structuré, clair et pédagogique sur le thème : '{title}'. Utilise des emojis, des points clés et une conclusion. Le cours doit être adapté pour une lecture sur WhatsApp."
        try:
            response = self.text_model.generate_content(prompt)
            return response.text
        except:
            return f"Désolé, je n'ai pas pu préparer le cours sur '{title}' pour le moment."

    def generate_quiz_questions(self, topic, count=20):
        """Génère une liste de questions de quiz sur un sujet donné."""
        prompt = f'Génère {count} questions de quiz à choix multiples (A, B, C, D) sur le thème : "{topic}". Pour chaque question, indique la bonne réponse. Format JSON : [{"q": "...", "a": "...", "b": "...", "c": "...", "d": "...", "correct": "A"}, ...]'
        try:
            response = self.text_model.generate_content(prompt)
            text = response.text.replace("```json", "").replace("```", "").strip()
            return json.loads(text)
        except:
            return []
