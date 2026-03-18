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

def download_media(url, is_audio=False):
    """Télécharge une vidéo ou de l'audio via yt-dlp."""
    if not os.path.exists(DOWNLOAD_FOLDER):
        os.makedirs(DOWNLOAD_FOLDER)

    unique_id = str(uuid.uuid4())[:8]
    
    # Si l'URL ne commence pas par http, on considère que c'est une recherche
    if not url.startswith('http'):
        url = f"ytsearch1:{url}"

    ydl_opts = {
        'format': 'bestaudio/best' if is_audio else 'best[ext=mp4]/best',
        'outtmpl': f'{DOWNLOAD_FOLDER}/{unique_id}_%(title)s.%(ext)s',
        'noplaylist': True,
        'max_filesize': 50 * 1024 * 1024, # Limite à 50MB pour WhatsApp
        'quiet': True,
        'no_warnings': True
    }

    if is_audio:
        ydl_opts['postprocessors'] = [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }]

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            if 'entries' in info:
                # C'est un résultat de recherche
                info = info['entries'][0]
            
            filename = ydl.prepare_filename(info)
            if is_audio:
                # yt-dlp change l'extension après le post-processing
                filename = os.path.splitext(filename)[0] + ".mp3"

            return {
                "status": "success",
                "title": info.get('title', 'Média'),
                "file_path": filename,
                "type": "audio" if is_audio else "video"
            }
    except Exception as e:
        return {"status": "error", "message": str(e)}
