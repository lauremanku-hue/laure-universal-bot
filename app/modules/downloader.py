
import os
import yt_dlp
import uuid
import re

# Dossier de téléchargement à la racine
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../"))
DOWNLOAD_FOLDER = os.path.join(BASE_DIR, 'downloads')

def validate_url(url):
    """Vérifie si l'URL est un format supporté (YouTube, FB, IG)."""
    if not url:
        return False
    # Regex simplifiée et sécurisée pour éviter les SyntaxWarning
    youtube_regex = r"(https?://)?(www\.)?(youtube|youtu|youtube-nocookie)\.(com|be)/(watch\?v=|embed/|v/|.+\?v=)?([^&=%\?]{11})"
    
    is_youtube = re.match(youtube_regex, url) is not None
    is_social = any(x in url for x in ["facebook.com", "instagram.com", "tiktok.com"])
    
    return is_youtube or is_social

def download_media(url):
    """Télécharge une vidéo via yt-dlp."""
    if not os.path.exists(DOWNLOAD_FOLDER):
        os.makedirs(DOWNLOAD_FOLDER)

    unique_id = str(uuid.uuid4())[:8]
    
    ydl_opts = {
        'format': 'best[ext=mp4]/best',
        'outtmpl': f'{DOWNLOAD_FOLDER}/{unique_id}_%(title)s.%(ext)s',
        'noplaylist': True,
        'max_filesize': 150 * 1024 * 1024, # Limite à 50MB pour WhatsApp
        'quiet': True,
        'no_warnings': True
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            filename = ydl.prepare_filename(info)
            return {
                "status": "success",
                "title": info.get('title', 'Vidéo'),
                "file_path": filename,
                "type": "video"
            }
    except Exception as e:
        return {"status": "error", "message": str(e)}

