from pythonosc.udp_client import SimpleUDPClient
from backend.api.websocket_manager import ws_manager
import os
import json
import soundfile as sf
from backend.config import STATIC_AUDIO_DIR

# OSC Client Setup
OSC_IP = "127.0.0.1"  
OSC_PORT = 7400  
osc_client = SimpleUDPClient(OSC_IP, OSC_PORT)

USER_DATA_FILE = "user_data.json"

def load_user_data():
    """Load the latest user data."""
    if os.path.exists(USER_DATA_FILE):
        with open(USER_DATA_FILE, "r") as f:
            return json.load(f)
    return {}

#saves text to user_data.json under the correct key format, otherwise increments
def save_to_user_data(phase, speaker, text, index=None):
    user_data = load_user_data()
    user = user_data.get("user", {})

    key_type = "user_input" if speaker == "user" else "maia_output"
    key_prefix = f"{phase}.{key_type}"
    
    if index is None:
        existing_keys = [k for k in user.keys() if k.startswith(key_prefix)]
        next_id = len(existing_keys) + 1
        key = f"{key_prefix}_{next_id}"
    else:
        key = f"{key_prefix}_{index}"
    
    user[key] = text
    user_data["user"] = user

    with open(USER_DATA_FILE, "w") as f:
        json.dump(user_data, f, indent=4)

    print(f"✅ Saved to user_data.json: {key} -> {text}")

# WebSockets
async def broadcast(message: dict):
    """Send a message to all WebSocket clients using the WebSocketManager."""
    try:
        await ws_manager.broadcast(message)
    except Exception as e:
        print(f"⚠️ WebSocket Broadcast Error: {e}")

# WAV file duration - Returns duration of a WAV file in seconds as float.
def get_wav_duration(file_path: str, fallback: float = 5.0) -> float:

    absolute_path = (
        file_path if os.path.isabs(file_path)
        else os.path.join(STATIC_AUDIO_DIR, os.path.basename(file_path))
    )

    try:
        with sf.SoundFile(absolute_path) as f:
            return len(f) / f.samplerate
    except Exception as e:
        print(f"⚠️ Error reading WAV duration: {e} (Path Tried: {absolute_path})")
        return fallback

def set_user_name(name):
    user_data = load_user_data()
    user_data["userName"] = name
    with open(USER_DATA_FILE, "w") as f:
        json.dump(user_data, f, indent=4)
    print(f"✅ Set userName in user_data.json: {name}")
