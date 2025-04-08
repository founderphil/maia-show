import asyncio
import json
from fastapi import APIRouter
from pythonosc.udp_client import SimpleUDPClient
from backend.api.pipelines.tts_only import run_tts_only
from backend.api.websocket_manager import ws_manager
from backend.utils.utils import broadcast, save_to_user_data
from backend.config import USER_DATA_FILE, STATIC_AUDIO_DIR
import soundfile as sf

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

def get_wav_duration(file_path):
    """Returns duration of a WAV file in seconds."""
    absolute_path = os.path.join(STATIC_AUDIO_DIR, os.path.basename(file_path))  # Convert relative URL to absolute path
    try:
        with sf.SoundFile(absolute_path) as f:
            return len(f) / f.samplerate
    except Exception as e:
        print(f"⚠️ Error reading WAV duration: {e} (Path Tried: {absolute_path})")
        return 5  

## THIS IS RESET POSITION
router.post("/start_tablet") #TODO: move the intro TTS inference to this endpoint
async def start_tablet_phase():
    print("🚀 Starting Show!")
######## set the lights
    await asyncio.sleep(1)
    print("Go Cue 1 - Lights, Reset Tablet, Play Music")
    lighting_cues = {
        "maiaLED": 0, # 0-255
        "houseLight1": 1, #0 or 1, on off
        "houseLight2": 1,
        "floorLight1": 1,
        "floorLight2": 1,
        "deskLight": 1,
        "chairSpot": 0,
        "maiaProjector1": 0,
    }
    for light, value in lighting_cues.items():
        client.send_message(f"/lighting/{light}", value) ######## play soundtrack
    await asyncio.sleep(1)

    client.send_message("/audio/play/music/", "soundtrack")

    asyncio.create_task(run_tts_only())  # fire and forget TTS
    return {"message": "Tablet Phase Started"}

@router.post("/run_tablet_tts")
async def run_tablet_tts():
    print("🔊 Running TTS Welcome from Tablet Phase")

    tts_results = await run_tts_only(filename="maia_output_welcome.wav") 
    print("✅ Tablet Phase TTS result:", tts_results)

    save_to_user_data("intro", "maia", tts_results["llm_response"])
    welcome_audio_path = tts_results.get("audio_url")
    
    if welcome_audio_path:
        audio_duration = get_wav_duration(welcome_audio_path)
        print(f"📏 Detected WAV duration: {audio_duration} seconds")
    else:
        print("⚠️ No audio file found for measuring duration!")
        audio_duration = 5  

    await asyncio.sleep(max(audio_duration, 1)) ######## wait for welcome to finish

    ws_message = {
        "type": "tts_audio_only",
        "user_name": tts_results.get("user_name", "Unknown"),
        "chosen_signet": tts_results.get("chosen_signet", "?"),
        "audio_url": tts_results.get("audio_url", ""),
        "llm_response": tts_results.get("text", ""),
    }

    try:
        await broadcast(ws_message)
        print("📡 Sent Tablet TTS WebSocket:", ws_message)
    except Exception as e:
        print(f"⚠️ WebSocket error in /run_tablet_tts: {e}")

    return {"message": "Tablet TTS Complete", **ws_message}


@router.post("/activate") ######## pressing the button on the tablet moves to next phase
async def activate():
    """✨ Final step when user presses 'Activate' in Tablet UI."""
    print("✨ User pressed Activate! Advancing to Phase 2 - Introduction.")
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