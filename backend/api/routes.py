from fastapi import APIRouter
from backend.api.phases.tablet_phase import reset_room
from backend.api.phases.intro_phase import start_intro_phase
from backend.api.phases.lore_phase import start_lore_phase, audio_done_event
from backend.api.phases.assignment_phase import start_assignment_phase
from backend.api.phases.depart_phase import start_departure_phase
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


PHASE_FUNCTIONS = {
    "reset": reset_room,
    # "tablet": start_tablet_phase,  ###Removed endpoint for now - really was used for debugging
    "intro": start_intro_phase,
    "lore": start_lore_phase,
    "assignment": start_assignment_phase,
    "departure": start_departure_phase,
}

@router.post("/start_phase")
async def start_phase(data: dict):
    phase = data.get("phase")
    print(f"🔄 User changed phases to: {phase}")

    if phase in PHASE_FUNCTIONS:
        response = await PHASE_FUNCTIONS[phase]()
        if response is None:
            response = {}
        await ws_manager.broadcast({
            "type": f"phase_{phase}",
            "phase": phase,
            "message": f"Phase '{phase}' started"
        })
        return {"message": f"Phase '{phase}' started successfully", **response}

    return {"error": f"Phase '{phase}' does not exist."}

@router.post("/osc/audio_done")
async def handle_audio_done():
    print("✅ MAX MSP: Audio playback done signal received")
    audio_done_event.set()
    return {"status": "received"}
