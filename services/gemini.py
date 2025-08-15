# services/gemini.py
import requests
import logging

from config import Config

logger = logging.getLogger(__name__)

def generate_response(contents):
    """
    Calls Google's Gemini API to generate a response.
    'contents' can be a single text string or a list of message objects for multi-turn conversations.
    """
    if not Config.GOOGLE_API_KEY:
        raise ValueError("Google API key is not configured.")

    url = f"https://generativelanguage.googleapis.com/v1beta/models/{Config.GEMINI_MODEL}:generateContent"
    
    headers = {
        'Content-Type': 'application/json',
        'X-goog-api-key': Config.GOOGLE_API_KEY
    }
    
    if isinstance(contents, str):
        data = {'contents': [{'parts': [{'text': contents}]}]}
    elif isinstance(contents, list):
        data = {'contents': contents}
    else:
        raise TypeError("Gemini API 'contents' must be a string or a list.")
    
    try:
        logger.info("Calling Gemini API...")
        response = requests.post(url, headers=headers, json=data)
        response.raise_for_status()
        response_json = response.json()
        
        # Safely extract the text from the response
        llm_response_text = response_json['candidates'][0]['content']['parts'][0]['text']
        logger.info("Gemini API call successful.")
        return llm_response_text
    except requests.exceptions.HTTPError as err:
        logger.error(f"Gemini API HTTP Error: {err.response.status_code} - {err.response.text}", exc_info=True)
        raise ValueError(f"LLM API request failed with status {err.response.status_code}.") from err
    except (KeyError, IndexError) as e:
        logger.error(f"Failed to parse Gemini response: {e}", exc_info=True)
        raise ValueError("Invalid response format from LLM.") from e