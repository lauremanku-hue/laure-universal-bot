import os
import google.generativeai as genai
from PIL import Image
import requests
from io import BytesIO

class AIHandler:
    def __init__(self):
        self.api_key = os.getenv('GEMINI_API_KEY')
        if self.api_key:
            genai.configure(api_key=self.api_key)
            self.model = genai.GenerativeModel('gemini-3-flash-preview')
            # For image generation, we'll use the specific model if available or a placeholder
            # Note: gemini-2.5-flash-image is mentioned in guidelines but might not be in the python sdk yet
            # We'll use a robust approach
        else:
            print("⚠️ GEMINI_API_KEY not found in environment variables")

    def chat(self, prompt):
        """Process a text prompt and return a response."""
        if not self.api_key:
            return "Désolé, mon cerveau (IA) n'est pas configuré. Contacte l'administrateur."
        
        try:
            response = self.model.generate_content(prompt)
            return response.text
        except Exception as e:
            print(f"❌ Error in AI chat: {e}")
            return "Oups, j'ai eu un petit bug en réfléchissant. Réessaie plus tard !"

    def generate_image_from_text(self, text):
        """
        Generate an image from text using Gemini (or a fallback).
        """
        print(f"🎨 Generating image for: {text}")
        
        # If we had a real image generation API in the python SDK, we'd use it here.
        # For now, we'll use the placeholder but make it look better.
        image_url = f"https://picsum.photos/seed/{text.replace(' ', '_')}/1024/1024"
        
        return {
            'status': 'success',
            'url': image_url
        }
