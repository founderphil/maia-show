#standarize the paths for the project
import os

# Base directory /maia-show/
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..")) 
print(BASE_DIR)

#Static Directory
STATIC_DIR = os.path.join(BASE_DIR, "static")  # Use `/static/`
STATIC_AUDIO_DIR = os.path.join(STATIC_DIR, "audio")
STATIC_IMAGE_DIR = os.path.join(STATIC_DIR, "images")  # For captured.png
print(STATIC_IMAGE_DIR)
print(STATIC_AUDIO_DIR)
print(STATIC_DIR)

#Models
MODELS_DIR = os.path.join(BASE_DIR, "backend/models")
STT_TTS_DIR = os.path.join(MODELS_DIR, "stt_tts")
VISION_DIR = os.path.join(MODELS_DIR, "vision")

#Speaker Reference Audio
SPEAKER_WAV = os.path.join(STT_TTS_DIR, "patricia_full.wav")

#User Data File
USER_DATA_FILE = os.path.join(BASE_DIR, "user_data.json")


os.makedirs(STATIC_AUDIO_DIR, exist_ok=True)
os.makedirs(STATIC_IMAGE_DIR, exist_ok=True)