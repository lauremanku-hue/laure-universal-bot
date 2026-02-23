import requests
import random

class EntertainmentModule:
    def __init__(self):
        self.riddles = [
            {"q": "Je suis grand quand je suis jeune et petit quand je suis vieux.", "a": "Une bougie"},
            {"q": "Qu'est-ce qui a des dents mais ne peut pas mordre ?", "a": "Un peigne"},
            {"q": "Plus il y en a, moins on voit.", "a": "L'obscurité"},
            {"q": "Plus je sèche, plus je deviens mouillé.", "a": "Une serviette"}
        ]

    def get_online_joke(self):
        url = "https://api.blablagues.net/?rub=blagues"
        try:
            r = requests.get(url, timeout=5)
            if r.status_code == 200:
                data = r.json()
                content = data["data"]["content"]
                text = content.get('text_head', '') + "\n" + content.get('text', '')
                return f"😂 **Blague :**\n{text.strip()}"
            return "C'est un mec qui entre dans un café... et PLOUF."
        except:
            return "⚠️ Problème de blague."

    def get_riddle(self):
        riddle = random.choice(self.riddles)
        return {"question": riddle['q'], "answer": riddle['a']}

# --- HELPER POUR LE SCRIPT DE TEST ---
def get_random_riddle():
    ent = EntertainmentModule()
    res = ent.get_riddle()
    return f"🤔 **Devinette :** {res['question']}\n\n||Réponse : {res['answer']}||"


