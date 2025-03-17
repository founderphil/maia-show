from fastapi import APIRouter
from backend.api.phases.tablet_phase import start_tablet_phase
from backend.api.phases.intro_phase import start_intro_phase
from backend.api.websocket_manager import ws_manager
import json
import os
from pythonosc.udp_client import SimpleUDPClient

router = APIRouter()
USER_DATA_FILE = "user_data.json" 
OSC_IP = "127.0.0.1"
OSC_PORT = 7400
client = SimpleUDPClient(OSC_IP, OSC_PORT)

def load_user_data():
    if os.path.exists(USER_DATA_FILE):
        with open(USER_DATA_FILE, "r") as f:
            return json.load(f)
    return {}

@router.get("/users")
async def get_users():
    """Retrieve stored user data (latest user only)."""
    if not os.path.exists(USER_DATA_FILE):
        return {"error": "No user data found"}

    try:
        with open(USER_DATA_FILE, "r") as f:
            user_data = json.load(f)

        return {"user": user_data.get("user", {})} 
    except json.JSONDecodeError:
        return {"error": "Failed to parse user data"}

@router.post("/save_user")
async def save_user(user_data: dict):
    """Save user data by updating the latest user instead of creating multiple records."""
    print(f"Saving user data: {user_data}")

    existing_data = {}
    
    
    if os.path.exists(USER_DATA_FILE):
        try:
            with open(USER_DATA_FILE, "r") as f:
                existing_data = json.load(f)
        except json.JSONDecodeError:
            print("Error: Could not parse user data file.")
            existing_data = {}

    existing_data["user"] = {**existing_data.get("user", {}), **user_data}
 
    with open(USER_DATA_FILE, "w") as f:
        json.dump(existing_data, f, indent=4)

    return {"message": "User data saved successfully", "user": existing_data["user"]}


# API endpoint to activate Phase 2 (Introduction)
@router.post("/start_intro")
async def start_intro():
    print("🚀 Starting Phase 2: Introduction")

    # Send OSC message to MAX MSP to start Phase 2
    client.send_message("/phase/intro", 1)
    # Cue 4: Play Preshow Voice
    # Cue 5: Stop Preshow Voice if Tablet picked up
    client.send_message("/audio/stop", "Preshow_Voice_1.wav")

    # Increase music volume to 50%
    client.send_message("/audio/play", ["Majo.mp3", 0.50])

    # Send WebSocket Message to UI to update phase
    await ws_manager.broadcast({
        "type": "phase_change",
        "phase": "intro"
    })

    return {"message": "Phase 2 (Introduction) started"}

@router.post("/start_phase")  # ✅ Ensure this is registered
async def start_phase(data: dict):
    phase = data.get("phase")
    print(f"🔄 User changed phases to: {phase}")

    if phase == "tablet":
        return await start_tablet_phase()
    else:
        return {"message": f"Phase '{phase}' does not have a defined action"}