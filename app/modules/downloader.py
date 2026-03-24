import os
import yt_dlp
import 

def download_media(query, is_audio=True):
    """
    Search and download media (audio or video) from a query using yt-dlp.
    """
    print(f"📥 Downloading {'audio' if is_audio else 'video'} for: {query}")
    
    # Ensure downloads directory exists
    download_dir = "downloads"
    if not os.path.exists(download_dir):
        os.makedirs(download_dir)

    # Search query on YouTube
    search_query = f"ytsearch1:{query}"
    
    # yt-dlp options
    ydl_opts = {
        'format': 'bestaudio/best' if is_audio else 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best',
        'outtmpl': f'{download_dir}/%(title)s.%(ext)s',
        'noplaylist': True,
        'quiet': True,
        'no_warnings': True,
    }

    if is_audio:
        ydl_opts['postprocessors'] = [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }]

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            # Extract info and download
            info = ydl.extract_info(search_query, download=True)
            if 'entries' in info:
                video_info = info['entries'][0]
            else:
                video_info = info
            
            # Get file path
            filename = ydl.prepare_filename(video_info)
            if is_audio:
                # If audio, the filename might have changed to .mp3
                filename = os.path.splitext(filename)[0] + ".mp3"
            
            return {
                'status': 'success',
                'file_path': filename,
                'title': video_info.get('title', 'Unknown')
            }
    except Exception as e:
        print(f"❌ Error in downloader: {e}")
        return {
            'status': 'error',
            'message': f"Erreur lors du téléchargement : {str(e)}"
        }
