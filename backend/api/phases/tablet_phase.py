"""
Phase 1- TABLET
1. Light cue 1
    MAIA LED : OFF 
    HOUSE LIGHT 1 : ON 100%
    HOUSE LIGHT 2 : ON 100%
    CHAIR SPOT : OFF
    MAIA SPOT 1 : OFF
    MAIA SPOT 2 : OFF
    MAIA PROJECTOR 1 : OFF
    MAIA PROJECTOR 2: OFF
2. Play music MAJO.WAV at 25% volume
3. HOST “TABLET UI” LOCALLY
PLAY AUDIO: PRESHOW_VOICE_1 WAV FILE, on “TABLET UI” 
IF TABLET PICKED UP, STOP PRESHOW_VOICE_1 WAV FILE
“Tablet UI” input field, “what can i call you?”; SAVE VALUE TO FIELD: profile_data.NAME
“Tablet UI” asks, “what calls to you”, user selects color;SAVE VALUE TO FIELD: profile_data.COLOR
Tablet UI asks, “what calls to you”, user selects signet. SAVE VALUE TO FIELD: profile_data.SIGNET
Activate button is now show on “TABLET UI” activated
User presses activate; START Phase 2 - Introduction; OSC INTRO.START SIGNAL TO CHANGE FROM 0 TO 1
Play music MAJO.WAV at 50% volume

"""


import asyncio
from fastapi import APIRouter
from pythonosc.udp_client import SimpleUDPClient

router = APIRouter()

# OSC Client Setup
OSC_IP = "127.0.0.1"
OSC_PORT = 7400
client = SimpleUDPClient(OSC_IP, OSC_PORT)

@router.post("/start_tablet")
async def start_tablet_phase():
    print("🚀 Starting Phase 1: Tablet")

    # Cue 1: Set initial lighting state
    print("Go Light Cue 1")
    client.send_message("/lighting/maiaLED", float(0))
    client.send_message("/lighting/houseLight1", float(100))
    client.send_message("/lighting/houseLight2", float(100))
    client.send_message("/lighting/chairSpot", float(0))
    client.send_message("/lighting/maiaSpot1", float(0))
    client.send_message("/lighting/maiaSpot2", float(0))
    client.send_message("/lighting/maiaProjector1", float(0))
    client.send_message("/lighting/maiaProjector2", float(0))

    await asyncio.sleep(1) 

    # Cue 2: Play Music at 25%
    print("Go Music Cue 1")
    client.send_message("/audio/play", ["Majo.mp3", float(0.25)])

    # Cue 3: Open Tablet UI
    print("Go Reset Tablet to 1")
    client.send_message("/ui/open", "tablet") #maybe this is not needed

    return {"message": "Tablet Phase Started"}

@router.post("/save_user")
async def save_user(user_data: dict):
    print(f"User Data Saved: {user_data}")
    # Save to a local JSON file or in-memory database
    with open("user_data.json", "w") as f:
        import json
        json.dump(user_data, f)

    return {"message": "User data saved successfully"}

# API endpoint to activate Phase 2 (Introduction)
@router.post("/activate")
async def activate():
    print("✅ Activating Phase 2: Introduction")
    
    # Send OSC signal to MAX MSP
    client.send_message("/phase/intro", 1)
    
    # Increase music volume to 50%
    client.send_message("/audio/play", ["Majo.mp3", 0.50])

    return {"message": "Phase 2 started"}