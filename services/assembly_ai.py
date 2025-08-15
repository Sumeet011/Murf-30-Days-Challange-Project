# services/assembly_ai.py
import requests
import time
import logging

from config import Config

logger = logging.getLogger(__name__)

def is_allowed_file(filename):
    """Checks if the file extension is allowed."""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in Config.ALLOWED_EXTENSIONS

def _upload_audio(audio_data):
    """Uploads audio file to AssemblyAI and returns the upload URL."""
    if not Config.ASSEMBLY_AI_API_KEY:
        raise ValueError("AssemblyAI API key is not set.")
    
    headers = {
        'authorization': Config.ASSEMBLY_AI_API_KEY,
        'content-type': 'application/octet-stream'
    }
    
    response = requests.post(Config.ASSEMBLY_AI_UPLOAD_URL, data=audio_data, headers=headers)
    response.raise_for_status()
    return response.json()['upload_url']

def _request_transcription(audio_url):
    """Requests transcription from AssemblyAI and returns the transcript ID."""
    if not Config.ASSEMBLY_AI_API_KEY:
        raise ValueError("AssemblyAI API key is not set.")

    headers = {
        'authorization': Config.ASSEMBLY_AI_API_KEY,
        'content-type': 'application/json'
    }
    
    data = {
        'audio_url': audio_url,
        'language_detection': True,
        'punctuate': True,
        'format_text': True
    }
    
    response = requests.post(Config.ASSEMBLY_AI_TRANSCRIPT_URL, json=data, headers=headers)
    response.raise_for_status()
    return response.json()['id']

def _get_transcription_result(transcript_id):
    """Polls for transcription completion and returns the transcribed text."""
    if not Config.ASSEMBLY_AI_API_KEY:
        raise ValueError("AssemblyAI API key is not set.")
    
    headers = {'authorization': Config.ASSEMBLY_AI_API_KEY}
    max_attempts = 30  # 5 minutes max (30 * 10s)
    attempt = 0
    
    while attempt < max_attempts:
        response = requests.get(f"{Config.ASSEMBLY_AI_TRANSCRIPT_URL}/{transcript_id}", headers=headers)
        response.raise_for_status()
        result = response.json()
        
        if result['status'] == 'completed':
            return result['text']
        elif result['status'] == 'error':
            raise Exception(f"Transcription failed: {result.get('error', 'Unknown error')}")
        
        time.sleep(10)
        attempt += 1
    
    raise TimeoutError("Transcription timeout")

def transcribe_audio(audio_data):
    """
    Main function to orchestrate the transcription process.
    Handles upload, transcription request, and polling for the result.
    """
    try:
        logger.info("Starting AssemblyAI transcription process.")
        audio_url = _upload_audio(audio_data)
        transcript_id = _request_transcription(audio_url)
        transcription = _get_transcription_result(transcript_id)
        logger.info("AssemblyAI transcription successful.")
        return transcription
    except Exception as e:
        logger.error(f"AssemblyAI transcription failed: {e}", exc_info=True)
        raise ValueError("Failed to transcribe audio.") from e