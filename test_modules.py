
import unittest
import os
import sys

# On s'assure que Python trouve le dossier 'app'
sys.path.append(os.path.dirname(os.path.abspath(__file__)))


from app.modules.education import get_educational_content, EducationModule
from app.modules.entertainment import get_random_riddle, EntertainmentModule
from app.modules.downloader import validate_url, download_media


class TestLaureModules(unittest.TestCase):

    def test_1_education(self):
        print("\n[TEST] Education (Wiki)...")
        res = get_educational_content("Python (langage)")
        self.assertIn("Python", res)
        print("✅ Wiki OK")

    def test_2_quiz(self):
        print("[TEST] Education (Quiz)...")
        edu = EducationModule()
        res = edu.get_online_quiz("science")
        self.assertIsInstance(res, dict)
        self.assertIn("question", res)
        print("✅ Quiz OK")

    def test_3_entertainment(self):
        print("[TEST] Divertissement...")
        res = get_random_riddle()
        self.assertIn("🤔", res)
        print("✅ Devinette OK")

    def test_4_downloader_validation(self):
        print("[TEST] Validation URL...")
        valid = validate_url("https://www.youtube.com/watch?v=dQw4w9WgXcQ")
        self.assertTrue(valid)
        print("✅ Validation OK")

    def test_5_downloader_real(self):
        print("[TEST] Téléchargement réel (vidéo très courte)...")
        # Vidéo de 5 secondes pour ne pas ralentir le test
        url = "https://www.youtube.com/watch?v=jNQXAC9IVRw" 
        res = download_media(url)
        self.assertEqual(res["status"], "success")
        print(f"✅ Download OK : {res['file_path']}")

if __name__ == '__main__':
    print("🧪 --- DÉMARRAGE DES TESTS TECHNIQUES --- 🧪")
    unittest.main()

