# **Conversational AI Bot**

This project is a web-based conversational AI bot that allows users to interact using their voice. It uses a combination of Speech-to-Text (STT), a Large Language Model (LLM), and Text-to-Speech (TTS) to provide a seamless, voice-driven chat experience. The backend is built with Flask and is designed to be modular and maintainable.

### **✨ Features**

* **Voice Interaction**: Talk to the bot using your microphone.  
* **Speech-to-Text (STT)**: Transcribes your spoken words into text.  
* **Conversational AI**: Uses a powerful LLM to generate intelligent and context-aware responses.  
* **Text-to-Speech (TTS)**: Converts the bot's text responses back into natural-sounding speech.  
* **Session-based Chat History**: Maintains the conversation history for each user session, enabling multi-turn dialogues.  
* **Responsive Web Interface**: The user interface is a single-page application with a clean, modern design that works well on different screen sizes.

### **🛠️ Technologies Used**

* **Backend Framework**: **Flask**  
* **Data Validation**: **Pydantic**  
* **Environment Management**: **python-dotenv**  
* **Speech-to-Text**: **AssemblyAI API**  
* **Large Language Model**: **Google Gemini API** (gemini-2.0-flash)  
* **Text-to-Speech**: **Murf AI API**  
* **Frontend**: HTML, CSS, and JavaScript

### **🏗️ Project Architecture**

The project follows a clean, modular architecture to separate concerns and enhance maintainability.

* app.py: The main entry point of the application. It handles routing, coordinates the flow between different services, and serves the frontend HTML page.  
* config.py: Centralized configuration management. All API keys, service URLs, and application settings are stored here, sourced from a .env file.  
* services/: A directory containing modules for each third-party service.  
  * assembly\_ai.py: Logic for uploading and transcribing audio.  
  * gemini.py: Logic for communicating with the Gemini API.  
  * murf.py: Logic for generating speech and creating the fallback audio file.

This structure makes it easy to swap out services or add new features without cluttering the main application logic.

### **🚀 Getting Started**

Follow these steps to set up and run the application locally.

#### **Prerequisites**

* Python 3.8 or higher  
* An active AssemblyAI API key  
* An active Murf AI API key  
* An active Google API key

#### **1\. Clone the repository**

git clone \<repository\_url\>  
cd \<project\_directory\>

#### **2\. Set up a virtual environment and install dependencies**

python \-m venv venv  
source venv/bin/activate  \# On Windows, use \`venv\\Scripts\\activate\`  
pip install \-r requirements.txt

#### **3\. Create and configure the .env file**

Create a file named .env in the root of your project and add the following environment variables. Replace the placeholder values with your actual API keys.

ASSEMBLY\_AI\_API\_KEY="your\_assembly\_ai\_api\_key"  
MURF\_API\_KEY="your\_murf\_ai\_api\_key"  
GOOGLE\_API\_KEY="your\_google\_api\_key"

FLASK\_DEBUG=True  
PORT=5000

#### **4\. Run the application**

Start the Flask server.

python app.py

The application will be running at http://localhost:5000. Open this URL in your web browser to start a conversation with the bot.