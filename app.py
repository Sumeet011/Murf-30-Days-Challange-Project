# app.py
from flask import Flask, request, jsonify, render_template_string, send_from_directory
from flask_cors import CORS
from pydantic import BaseModel, ValidationError
import logging
import os
import uuid
import tempfile

from config import Config
from services import assembly_ai, gemini, murf

# --- App Initialization and Configuration ---
app = Flask(__name__)
CORS(app)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# In-memory datastore for chat history
# Note: This is not persistent and will reset on server restart.
chat_history = {}

# Pydantic models for request and response validation
class ChatRequest(BaseModel):
    voice_id: str = 'natalie'

class ChatResponse(BaseModel):
    success: bool
    transcription: str
    llm_response: str
    audio_url: str

# --- Routes ---

@app.route('/')
def index():
    """Serves the main page with the conversational bot interface."""
    # The HTML template remains the same, so we'll omit it for brevity.
    # You can paste the original HTML here.
    html_template = '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Conversational Bot</title>
    <style>
        body { 
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif; 
            max-width: 800px; 
            margin: 0 auto; 
            padding: 20px; 
            background: linear-gradient(135deg, #1f1c2c 0%, #928dab 100%); 
            min-height: 100vh; 
            color: white; 
            display: flex;
            flex-direction: column;
        }
        .container { 
            background: rgba(255, 255, 255, 0.08); 
            border-radius: 20px; 
            padding: 30px; 
            backdrop-filter: blur(10px); 
            box-shadow: 0 8px 32px rgba(31, 38, 135, 0.37); 
            border: 1px solid rgba(255, 255, 255, 0.18);
            flex: 1;
            display: flex;
            flex-direction: column;
        }
        h1 { 
            text-align: center; 
            margin-bottom: 20px; 
            font-size: 2.5em; 
            text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
        }
        .session-info { 
            text-align: center; 
            margin-bottom: 20px; 
            font-size: 0.9em; 
            opacity: 0.8;
        }
        .conversation-history { 
            flex-grow: 1;
            overflow-y: auto;
            margin-bottom: 20px;
            padding: 10px;
            border-radius: 10px;
            background: rgba(0, 0, 0, 0.2);
            display: flex;
            flex-direction: column;
            gap: 15px;
        }
        .message-bubble { 
            padding: 15px; 
            border-radius: 15px; 
            max-width: 80%;
            word-wrap: break-word;
            line-height: 1.6;
            animation: fadeIn 0.5s ease-in-out;
        }
        .user-message { 
            background: #5a5a72; 
            align-self: flex-end;
            border-bottom-right-radius: 5px;
        }
        .bot-message { 
            background: #474759; 
            align-self: flex-start;
            border-bottom-left-radius: 5px;
        }
        .message-bubble strong {
            font-weight: 600;
        }
        
        .controls {
            display: flex;
            flex-direction: column;
            align-items: center;
            gap: 20px;
            margin-top: 20px;
        }
        
        .record-btn-container {
            position: relative;
        }
        
        #recordBtn {
            width: 100px;
            height: 100px;
            border-radius: 50%;
            background: linear-gradient(45deg, #ff6b6b, #ee5a24);
            border: none;
            cursor: pointer;
            color: white;
            font-size: 1.2em;
            transition: all 0.3s ease;
            box-shadow: 0 4px 15px rgba(0,0,0,0.2);
            position: relative;
            z-index: 2;
        }
        
        #recordBtn:hover {
            transform: scale(1.05);
            box-shadow: 0 6px 20px rgba(0,0,0,0.3);
        }
        
        #recordBtn:disabled {
            background: #666;
            cursor: not-allowed;
            transform: none;
            opacity: 0.8;
        }

        #recordBtn.recording {
            background: linear-gradient(45deg, #e74c3c, #c0392b) !important;
            animation: pulse 1.5s infinite;
        }

        @keyframes pulse {
            0% { transform: scale(1); }
            50% { transform: scale(1.1); }
            100% { transform: scale(1); }
        }

        #recordBtn:active::before {
            content: '';
            position: absolute;
            top: -10px;
            left: -10px;
            right: -10px;
            bottom: -10px;
            background-color: rgba(255, 255, 255, 0.2);
            border-radius: 50%;
            animation: record-ring 1s cubic-bezier(0.23, 1, 0.32, 1) forwards;
            z-index: 1;
        }
        
        @keyframes record-ring {
            0% { transform: scale(0); opacity: 1; }
            100% { transform: scale(1.5); opacity: 0; }
        }

        .status { 
            padding: 15px; 
            margin-top: 15px; 
            border-radius: 10px; 
            border-left: 4px solid;
            font-size: 0.9em;
        }
        .error { border-left-color: #e74c3c; background: rgba(231, 76, 60, 0.1); }
        .success { border-left-color: #27ae60; background: rgba(39, 174, 96, 0.1); }
        .info { border-left-color: #3498db; background: rgba(52, 152, 219, 0.1); }
        .loading { 
            display: inline-block; 
            width: 20px; 
            height: 20px; 
            border: 3px solid rgba(255,255,255,0.3); 
            border-radius: 50%; 
            border-top-color: #fff; 
            animation: spin 1s ease-in-out infinite; 
            margin-right: 10px; 
        }
        @keyframes spin { to { transform: rotate(360deg); } }
        
        @keyframes fadeIn {
            from { opacity: 0; transform: translateY(10px); }
            to { opacity: 1; transform: translateY(0); }
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>🗣️ Conversational AI</h1>
        <div class="session-info">
            Session ID: <span id="sessionIdDisplay"></span>
        </div>
        
        <div class="conversation-history" id="conversation-history">
            <div class="message-bubble bot-message">
                <strong>Bot:</strong> Hello there! How can I help you today?
            </div>
        </div>

        <div class="controls">
            <div id="status"></div>
            <div class="record-btn-container">
                <button id="recordBtn" onclick="toggleRecording()">Start</button>
            </div>
        </div>

    </div>

    <script>
        let mediaRecorder;
        let recordedBlob;
        let audioChunks = [];
        let sessionId = '';
        let isPlaying = false;
        let isRecording = false;
        let audioPlayer = null;

        function getSessionId() {
            const urlParams = new URLSearchParams(window.location.search);
            let id = urlParams.get('session_id');
            if (!id) {
                id = crypto.randomUUID();
                window.history.pushState({}, '', `/?session_id=${id}`);
            }
            return id;
        }

        document.addEventListener('DOMContentLoaded', () => {
            sessionId = getSessionId();
            document.getElementById('sessionIdDisplay').textContent = sessionId;
        });

        async function toggleRecording() {
            const recordBtn = document.getElementById('recordBtn');
            
            if (isPlaying) {
                showStatus('Bot is speaking, please wait.', 'info');
                return;
            }

            if (isRecording) {
                // Stop recording logic
                isRecording = false;
                mediaRecorder.stop();
                mediaRecorder.stream.getTracks().forEach(track => track.stop());
                recordBtn.textContent = 'Processing...';
                recordBtn.classList.remove('recording');
                recordBtn.disabled = true;
                showStatus('Processing audio... This may take a few moments.', 'info', true);
            } else {
                // Start recording logic
                try {
                    const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
                    mediaRecorder = new MediaRecorder(stream);
                    
                    mediaRecorder.ondataavailable = event => {
                        audioChunks.push(event.data);
                    };
                    
                    mediaRecorder.onstop = () => {
                        recordedBlob = new Blob(audioChunks, { type: 'audio/wav' });
                        audioChunks = [];
                        processAudio();
                    };
                    
                    mediaRecorder.start();
                    isRecording = true;
                    recordBtn.textContent = 'Stop';
                    recordBtn.classList.add('recording');
                    showStatus('Recording...', 'info');
                    
                } catch (error) {
                    showStatus('Error accessing microphone: ' + error.message, 'error');
                }
            }
        }

        async function processAudio() {
            if (!recordedBlob) {
                showStatus('No audio to process', 'error');
                toggleRecording();
                return;
            }
            
            const formData = new FormData();
            formData.append('audio', recordedBlob, 'audio.wav');
            
            try {
                const response = await fetch(`/agent/chat/${sessionId}`, {
                    method: 'POST',
                    body: formData
                });

                if (!response.ok) {
                    throw new Error(`HTTP error! status: ${response.status}`);
                }

                const result = await response.json();
                
                if (result.error) {
                    showStatus(result.error, 'error');
                    
                    if (audioPlayer) {
                        audioPlayer.pause();
                        audioPlayer = null;
                    }

                    audioPlayer = new Audio('/fallback-audio');
                    audioPlayer.play();
                    isPlaying = true;
                    
                } else {
                    appendMessage('user', result.transcription);
                    appendMessage('bot', result.llm_response);
                    
                    if (audioPlayer) {
                        audioPlayer.pause();
                        audioPlayer = null;
                    }

                    audioPlayer = new Audio(result.audio_url);
                    audioPlayer.play();
                    isPlaying = true;

                    showStatus('Audio processed successfully!', 'success');
                }

                audioPlayer.onended = () => {
                    console.log('Bot response audio ended. Ready for new input.');
                    isPlaying = false;
                    const recordBtn = document.getElementById('recordBtn');
                    recordBtn.disabled = false;
                    recordBtn.textContent = 'Start';
                    recordBtn.classList.remove('recording');
                    showStatus('Click "Start" to record your next message.', 'info');
                };

            } catch (error) {
                showStatus('Error processing audio: ' + error.message, 'error');
                if (audioPlayer) {
                    audioPlayer.pause();
                    audioPlayer = null;
                }
                audioPlayer = new Audio('/fallback-audio');
                audioPlayer.play();
                isPlaying = true;
                audioPlayer.onended = () => {
                    isPlaying = false;
                    const recordBtn = document.getElementById('recordBtn');
                    recordBtn.disabled = false;
                    recordBtn.textContent = 'Start';
                    recordBtn.classList.remove('recording');
                    showStatus('Click "Start" to record your next message.', 'info');
                };
            }
        }
        
        function appendMessage(sender, text) {
            const historyDiv = document.getElementById('conversation-history');
            const messageDiv = document.createElement('div');
            messageDiv.className = `message-bubble ${sender}-message`;
            messageDiv.innerHTML = `<strong>${sender === 'user' ? 'You' : 'Bot'}:</strong> ${text}`;
            historyDiv.appendChild(messageDiv);
            historyDiv.scrollTop = historyDiv.scrollHeight;
        }

        function showStatus(message, type = 'info', loading = false) {
            const statusDiv = document.getElementById('status');
            let icon = '';
            if (loading) icon = '<div class="loading"></div>';
            else if (type === 'error') icon = '❌ ';
            else if (type === 'success') icon = '✅ ';
            else icon = 'ℹ️ ';
            
            statusDiv.innerHTML = `<div class="status ${type}">${icon}${message}</div>`;
        }
    </script>
</body>
</html>
    '''
    return render_template_string(html_template)

@app.route('/agent/chat/<session_id>', methods=['POST'])
def agent_chat(session_id: str):
    """
    Handles the main conversational flow.
    1. Transcribes audio using AssemblyAI.
    2. Uses Gemini with chat history to generate a response.
    3. Generates speech from the response using Murf AI.
    """
    try:
        # Pydantic validation for incoming request
        chat_request = ChatRequest(voice_id=request.form.get('voice_id', 'natalie'))
        
        if 'audio' not in request.files:
            return jsonify({'error': 'No audio file provided'}), 400
        
        audio_file = request.files['audio']
        if audio_file.filename == '':
            return jsonify({'error': 'No file selected'}), 400
        
        if not assembly_ai.is_allowed_file(audio_file.filename):
            return jsonify({'error': 'Invalid file format'}), 400

        logger.info(f"Received audio file for session {session_id}: {audio_file.filename}")
        audio_data = audio_file.read()
        
        # Step 1: Transcribe audio
        user_transcription = assembly_ai.transcribe_audio(audio_data)
        if not user_transcription.strip():
            return jsonify({'error': 'No speech detected in audio'}), 400

        logger.info(f"User transcription for session {session_id}: '{user_transcription}'")

        # Step 2: Call Gemini with the full chat history
        if session_id not in chat_history:
            chat_history[session_id] = []
        
        chat_history[session_id].append({'role': 'user', 'parts': [{'text': user_transcription}]})
        
        llm_response_text = gemini.generate_response(chat_history[session_id])
        logger.info(f"LLM generated response for session {session_id}: '{llm_response_text}'")

        chat_history[session_id].append({'role': 'model', 'parts': [{'text': llm_response_text}]})

        # Step 3: Generate speech with Murf AI
        murf_response = murf.generate_speech(llm_response_text, voice_id=chat_request.voice_id)
        audio_url = murf_response['audioFile']
        
        # Construct and validate the response using Pydantic
        response_data = ChatResponse(
            success=True,
            transcription=user_transcription,
            llm_response=llm_response_text,
            audio_url=audio_url
        )
        return jsonify(response_data.dict())

    except (ValidationError, ValueError) as e:
        logger.error(f"Validation Error or Bad Request: {e}")
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        logger.error(f"General Error in agent chat endpoint for session {session_id}: {str(e)}", exc_info=True)
        return jsonify({'error': 'An unexpected error occurred. ' + str(e)}), 500

@app.route('/fallback-audio', methods=['GET'])
def get_fallback_audio():
    """Serves the static fallback audio file."""
    audio_path = murf.generate_fallback_audio()
    if audio_path and os.path.exists(audio_path):
        return send_from_directory(os.path.dirname(audio_path), os.path.basename(audio_path), mimetype="audio/mpeg")
    else:
        return "Fallback audio not available", 500

if __name__ == '__main__':
    # Generate fallback audio on startup if needed
    murf.generate_fallback_audio()
    app.run(debug=Config.DEBUG, host='0.0.0.0', port=Config.PORT)