"""Handler for YouTube video downloads and MP3 conversion"""
import os
import logging
import shutil
from pathlib import Path
from yt_dlp import YoutubeDL

logger = logging.getLogger(__name__)


def get_ffmpeg_path() -> str:
    """Find ffmpeg path in the system."""
    # Try to find ffmpeg
    ffmpeg_path = shutil.which('ffmpeg')
    if ffmpeg_path:
        return ffmpeg_path
    
    # Common paths for Linux/Unix
    common_paths = ['/usr/bin/ffmpeg', '/usr/local/bin/ffmpeg', '/opt/ffmpeg/bin/ffmpeg']
    for path in common_paths:
        if os.path.exists(path):
            return path
    
    # If not found, return None (yt-dlp will try to find it)
    logger.warning("FFmpeg not found in common paths")
    return None


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
    
    ffmpeg_path = get_ffmpeg_path()
    
    ydl_opts = {
        'format': 'bestaudio/best',
        'noplaylist': True,  # Only download single video, not playlist
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }],
        'outtmpl': os.path.join(output_dir, '%(title)s.%(ext)s'),
        'quiet': False,
        'no_warnings': False,
    }
    
    # Add ffmpeg location if found
    if ffmpeg_path:
        ydl_opts['ffmpeg_location'] = ffmpeg_path
    
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
