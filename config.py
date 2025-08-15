# config.py
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class Config:
    """Application configuration settings."""
    DEBUG = os.getenv("FLASK_DEBUG", "True").lower() in ('true', '1', 't')
    PORT = int(os.getenv("PORT", 5000))

    # API Keys
    ASSEMBLY_AI_API_KEY = os.getenv("ASSEMBLY_AI_API_KEY")
    MURF_API_KEY = os.getenv("MURF_API_KEY")
    GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")

    # Service URLs
    ASSEMBLY_AI_UPLOAD_URL = 'https://api.assemblyai.com/v2/upload'
    ASSEMBLY_AI_TRANSCRIPT_URL = 'https://api.assemblyai.com/v2/transcript'
    MURF_API_URL = 'https://api.murf.ai/v1/speech/generate'
    MURF_VOICES_URL = 'https://api.murf.ai/v1/speech/voices'
    GEMINI_MODEL = "gemini-2.0-flash"

    # Other settings
    ALLOWED_EXTENSIONS = {'wav', 'mp3', 'mp4', 'm4a', 'webm', 'ogg'}