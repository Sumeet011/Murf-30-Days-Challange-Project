# services/murf.py
import requests
import logging
import os
import tempfile

from config import Config

logger = logging.getLogger(__name__)

def generate_speech(text, voice_id='natalie'):
    """Generates speech using Murf AI and returns the response JSON."""
    if not Config.MURF_API_KEY:
        raise ValueError("Murf API key is not set.")
    
    headers = {
        'api-key': Config.MURF_API_KEY,
        'Content-Type': 'application/json',
        'Accept': 'application/json'
    }
    
    data = {
        'text': text,
        'voiceId': voice_id,
        'audioFormat': 'MP3',
        'model': 'GEN2',
        'speed': 0,
        'pitch': 0,
        'channelType': 'MONO',
        'sampleRate': 24000
    }
    
    try:
        logger.info(f"Generating speech with Murf AI for voice_id: {voice_id}")
        response = requests.post(Config.MURF_API_URL, json=data, headers=headers)
        response.raise_for_status()
        
        murf_response = response.json()
        if 'audioFile' not in murf_response:
            raise ValueError("No audio URL returned from Murf AI.")
        
        logger.info("Murf AI speech generation successful.")
        return murf_response
    except requests.exceptions.HTTPError as err:
        logger.error(f"Murf API HTTP Error: {err.response.status_code} - {err.response.text}", exc_info=True)
        raise ValueError("Murf API request failed.") from err
    except Exception as e:
        logger.error(f"Murf speech generation failed: {e}", exc_info=True)
        raise ValueError("Failed to generate speech.") from e

def generate_fallback_audio():
    """Generates and saves a static fallback audio file if it doesn't exist."""
    text = "I'm having trouble connecting right now. Please try again later."
    audio_path = os.path.join(tempfile.gettempdir(), "fallback_audio.mp3")

    if os.path.exists(audio_path):
        logger.info("Fallback audio file already exists.")
        return audio_path

    logger.info("Generating fallback audio file...")
    try:
        murf_response = generate_speech(text, voice_id='natalie')
        audio_url = murf_response.get('audioFile')
        if not audio_url:
            logger.error("Murf did not return an audio file URL for fallback.")
            return None
        
        audio_response = requests.get(audio_url)
        audio_response.raise_for_status()
        
        with open(audio_path, 'wb') as f:
            f.write(audio_response.content)
        
        logger.info("Fallback audio file generated successfully.")
        return audio_path
    except Exception as e:
        logger.error(f"Failed to generate fallback audio: {e}", exc_info=True)
        return None