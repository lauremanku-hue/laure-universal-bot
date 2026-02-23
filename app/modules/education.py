import requests
import html
import random

class EducationModule:
    def __init__(self):
        self.quiz_categories = {"it": 18, "science": 17, "histoire": 23, "geo": 22, "general": 9}

    def get_wiki_summary(self, topic):
        if not topic: return "Précise un sujet."
        formatted_topic = topic.replace(" ", "_").capitalize()
        url = f"https://fr.wikipedia.org/api/rest_v1/page/summary/{formatted_topic}"
        try:
            r = requests.get(url, timeout=10)
            if r.status_code == 200:
                data = r.json()
                title = data.get('title', topic)
                extract = data.get('extract', 'Pas de résumé.')
                link = data.get('content_urls', {}).get('desktop', {}).get('page', '')
                return f"📚 **{title}**\n\n{extract}\n\n🔗 {link}"
            return f"❌ Sujet '{topic}' non trouvé."
        except Exception as e:
            return f"⚠️ Erreur Wiki : {str(e)}"
    def get_online_quiz(self, topic="general"):
        cat_id = self.quiz_categories.get(topic.lower(), 9)
        url = f"https://opentdb.com/api.php?amount=1&category={cat_id}&type=multiple"
        try:
            r = requests.get(url, timeout=10)
            data = r.json()
            if data["response_code"] == 0:
                q = data["results"][0]
                options = [html.unescape(a) for a in q["incorrect_answers"]] + [html.unescape(q["correct_answer"])]
                random.shuffle(options)
                return {
                    "question": html.unescape(q["question"]),
                    "options": options,
                    "answer": html.unescape(q["correct_answer"])
                }
            return "❌ Pas de quiz disponible."
        except:
            return "⚠️ Erreur API Quiz."

# --- HELPER POUR LE SCRIPT DE TEST ---
def get_educational_content(topic="linux"):
    edu = EducationModule()
    return edu.get_wiki_summary(topic)


    def get_online_quiz(self, topic="general"):
        cat_id = self.quiz_categories.get(topic.lower(), 9)
        url = f"https://opentdb.com/api.php?amount=1&category={cat_id}&type=multiple"
        try:
            r = requests.get(url, timeout=10)
            data = r.json()
            if data["response_code"] == 0:
                q = data["results"][0]
                options = [html.unescape(a) for a in q["incorrect_answers"]] + [html.unescape(q["correct_answer"])]
                random.shuffle(options)
                return {
                    "question": html.unescape(q["question"]),
                    "options": options,
                    "answer": html.unescape(q["correct_answer"])
                }
            return "❌ Pas de quiz disponible."
        except:
            return "⚠️ Erreur API Quiz."

# --- HELPER POUR LE SCRIPT DE TEST ---
def get_educational_content(topic="linux"):
    edu = EducationModule()
    return edu.get_wiki_summary(topic)

