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

router = APIRouter()
USER_DATA_FILE = "user_data.json"

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

router.post("/start_tablet")
async def start_tablet_phase():
    print("🚀 Starting Phase 1: Tablet")

    print("🎭 Sending Lighting Cues to MAX MSP")
    client.send_message("/lighting/maiaLED", 0)
    client.send_message("/lighting/houseLight1", 100)
    client.send_message("/lighting/houseLight2", 100)
    client.send_message("/lighting/chairSpot", 0)
    client.send_message("/lighting/maiaSpot1", 0)
    client.send_message("/lighting/maiaSpot2", 0)
    client.send_message("/lighting/maiaProjector1", 0)
    client.send_message("/lighting/maiaProjector2", 0)

    await asyncio.sleep(1)

    # ✅ Send Music Command to MAX MSP
    print("🎵 Playing Majo.mp3 at 25% volume in MAX MSP")
    client.send_message("/audio/play", ["Majo.mp3", 0.25])

@router.post("/activate")
async def activate():
    """Final step when user presses 'Activate' in Tablet UI."""
    print("✨ User pressed Activate! Advancing to Phase 2 - Introduction.")

    # ✅ Increase Music Volume via MAX MSP
    client.send_message("/audio/soundtrack", ["Majo.mp3", 1])

    # ✅ Send OSC to trigger phase change in MAX MSP
    client.send_message("/phase/start", "intro")

    return {"message": "Phase 2 - Introduction Started"}