"""
Phase 1- TABLET
1.  Light cue 1
        MAIA LED : OFF 
        HOUSE LIGHT 1 : ON 100%
        HOUSE LIGHT 2 : ON 100%
        CHAIR SPOT : OFF
        MAIA SPOT 1 : OFF
        MAIA SPOT 2 : OFF
        MAIA PROJECTOR 1 : OFF
        MAIA PROJECTOR 2: OFF
2.  Play music MAJO.WAV at 25% volume
3.  HOST “TABLET UI” LOCALLY
4.  PLAY AUDIO: PRESHOW_VOICE_1 WAV FILE, on “TABLET UI” 
5.  IF TABLET PICKED UP, STOP PRESHOW_VOICE_1 WAV FILE
6.  “Tablet UI” input field, “what can i call you?”; SAVE VALUE TO FIELD: profile_data.NAME
7.  “Tablet UI” asks, “what calls to you”, user selects color;SAVE VALUE TO FIELD: profile_data.COLOR
8.  Tablet UI asks, “what calls to you”, user selects signet. SAVE VALUE TO FIELD: profile_data.SIGNET
9.  Activate button is now show on “TABLET UI” activated
10. User presses activate; START Phase 2 - Introduction; OSC INTRO.START SIGNAL TO CHANGE FROM 0 TO 1
11. Play music MAJO.WAV at 50% volume

"""

import asyncio
import json
from fastapi import APIRouter
from pythonosc.udp_client import SimpleUDPClient
from backend.api.websocket_manager import ws_manager
from backend.utils.utils import broadcast
from backend.config import USER_DATA_FILE, STATIC_AUDIO_DIR

import os
os.makedirs(STATIC_AUDIO_DIR, exist_ok=True)

router = APIRouter()

OSC_IP = "127.0.0.1"
OSC_PORT = 7400
client = SimpleUDPClient(OSC_IP, OSC_PORT)

def load_user_data():
    try:
        with open(USER_DATA_FILE, "r") as f:
            return json.load(f)
    except FileNotFoundError:
        return {}

def save_user_data(data):
    with open(USER_DATA_FILE, "w") as f:
        json.dump(data, f, indent=4)

router.post("/start_tablet") #TODO: move the intro TTS inference to this endpoint
async def start_tablet_phase():
    print("🚀 Starting Show!")
    
    #TODO: reset user data, do not load it, delete it all

    await asyncio.sleep(1)
    print("Go Cue 1 - Lights, Reset Tablet, Play Music")
    lighting_cues = {
        "maiaLED": 0,
        "houseLight1": 100,
        "houseLight2": 100,
        "chairSpot": 0,
        "maiaSpot1": 0,
        "maiaSpot2": 0,
        "maiaProjector1": 0,
        "maiaProjector2": 0,
    }
    for light, value in lighting_cues.items():
        client.send_message(f"/lighting/{light}", value)
    await asyncio.sleep(1)
    client.send_message("/audio/play", ["Majo.mp3", 0.25])

    return {"status": "Tablet Phase Started"}



@router.post("/activate")
async def activate():
    """✨ Final step when user presses 'Activate' in Tablet UI."""
    print("✨ User pressed Activate! Advancing to Phase 2 - Introduction.")


    client.send_message("/audio/play", ["Majo.mp3", 0.50])


    client.send_message("/phase/start", "intro")


    ws_message = {
    "type": "phase_tablet",
    "phase": "tablet",
    "message": "Phase 1 - Tablet Started"
    }
    await broadcast(ws_message)

    if ws_message is None:
        print("🚨 ERROR: WebSocket message is None!")
    else:
        print("📡 Sending WebSocket Message:", ws_message)
    try:
        await ws_manager.broadcast(ws_message)
    except Exception as e:
        print(f"⚠️ WebSocket Broadcast Error: {e}")