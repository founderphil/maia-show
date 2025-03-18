from pythonosc.udp_client import SimpleUDPClient
from backend.api.websocket_manager import WebSocketManager
import os
import json

ws_manager = WebSocketManager()

clients = set()

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

def save_to_user_data(phase, speaker, text):
    """
    Saves text to `user_data.json` under the correct key format:
    - `{phase}.user_input_X`  (for STT user inputs)
    - `{phase}.maia_output_X` (for TTS AI responses)
    """
    user_data = load_user_data()
    user = user_data.get("user", {})

    # standarized naming convention for user and maia outputs
    key_prefix = f"{phase}.{'user_input' if speaker == 'user' else 'maia_output'}"

    # Find the next available ID
    existing_keys = [k for k in user.keys() if k.startswith(key_prefix)]
    next_id = len(existing_keys) + 1
    key = f"{key_prefix}_{next_id}"

    # Save to JSON
    user[key] = text
    user_data["user"] = user

    with open(USER_DATA_FILE, "w") as f:
        json.dump(user_data, f, indent=4)

    print(f"✅ Saved to user_data.json: {key} -> {text}")

# Function to broadcast messages via WebSocket
async def broadcast(message: dict):
    """Broadcasts messages to all connected WebSocket clients."""
    import json
    for client in clients:
        try:
            await client.send_text(json.dumps(message))
        except Exception:
            clients.remove(client)