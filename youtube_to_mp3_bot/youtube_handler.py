"""Handler for YouTube video downloads and MP3 conversion"""
import os
import logging
from pathlib import Path
from yt_dlp import YoutubeDL

logger = logging.getLogger(__name__)


def download_youtube_as_mp3(url: str, output_dir: str = "downloads") -> str:
    """
    Download YouTube video and convert to MP3.
    
    Args:
        url: YouTube video URL
        output_dir: Directory to save MP3 files
        
    Returns:
        Path to the downloaded MP3 file
        
    Raises:
        Exception: If download fails
    """
    Path(output_dir).mkdir(exist_ok=True)
    
    ydl_opts = {
        'format': 'bestaudio/best',
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }],
        'outtmpl': os.path.join(output_dir, '%(title)s.%(ext)s'),
        'quiet': False,
        'no_warnings': False,
    }
    
    try:
        with YoutubeDL(ydl_opts) as ydl:
            logger.info(f"Downloading: {url}")
            info = ydl.extract_info(url, download=True)
            mp3_path = ydl.prepare_filename(info)
            # Replace extension with mp3
            mp3_path = mp3_path.rsplit('.', 1)[0] + '.mp3'
            logger.info(f"Successfully downloaded: {mp3_path}")
            return mp3_path
    except Exception as e:
        logger.error(f"Error downloading {url}: {str(e)}")
        raise


def is_valid_youtube_url(url: str) -> bool:
    """Check if URL is a valid YouTube URL"""
    return 'youtube.com' in url or 'youtu.be' in url
