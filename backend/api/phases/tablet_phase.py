import asyncio
import json
from fastapi import APIRouter
from pythonosc.udp_client import SimpleUDPClient
from backend.api.pipelines.tts_only import run_tts_only
from backend.api.pipelines.greetings_tts import tts_greeting
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
@router.post("/reset_room") 
async def reset_room():
    print("ROOM RESET")
######## set the lights
    await asyncio.sleep(1)
    print("Go Cue 1 - Lights, Reset Tablet, Play Music")
    lighting_cues = {
        "maiaLED": 0, # 0-255
        "floor": 1,
        "desk": 1,
        "projector": 0,
    }
    for light, value in lighting_cues.items():
        client.send_message(f"/lighting/{light}", value) 
    await asyncio.sleep(1)
######## play soundtrack
    client.send_message("/audio/volume/", -5)
    await asyncio.sleep(1)
    client.send_message("/audio/play/music/", "instrumental.wav") 
    print("Room reset complete")
    return {"message": "Room Reset"}

router.post("/start_tablet")
async def start_tablet_phase():
    print("🚀 Starting Show!")

    client.send_message("/audio/play/music/", "soundtrack")

    asyncio.create_task(tts_greeting()) ###inference takes 5 seconds
    asyncio.create_task(run_tts_only()) ###inference takes 35 seconds
    return {"message": "Tablet Phase Started"}
  

@router.post("/run_tablet_tts")
async def run_tablet_tts():
    print("🔊 Running TTS Welcome from Tablet Phase")

    tts_results = await tts_greeting(filename="maia_greeting.wav")
    print("✅ Tablet Phase TTS result:", tts_results)
    tts_results = await run_tts_only(filename="maia_output_welcome.wav")
    print("✅ Tablet Phase TTS result:", tts_results)

    save_to_user_data("intro", "maia", tts_results["llm_response"])    
    return {"message": "Tablet TTS Complete", **tts_results}


@router.post("/activate")
async def activate():
    print("✨ User pressed Activate!")
    
    # Send activation success message immediately
    ws_message = {
        "type": "activation_success",
        "phase": "tablet",
        "message": "Activation successful"
    }
    
    # Broadcast the message immediately
    try:
        print("📡 Sending WebSocket Message:", ws_message)
        await ws_manager.broadcast(ws_message)
        
        # Also broadcast the phase change message
        phase_message = {
            "type": "phase_tablet",
            "phase": "tablet",
            "message": "Phase 1 - Tablet Started"
        }
        await ws_manager.broadcast(phase_message)
    except Exception as e:
        print(f"⚠️ WebSocket Broadcast Error: {e}")
    
    # Start audio sequence in background
    asyncio.create_task(play_activation_audio_sequence())
    
    # Return immediately
    return {"success": True, "message": "Activation successful"}

async def play_activation_audio_sequence():
    """Play the activation audio sequence in the background."""
    try:
        # Check if greeting audio exists, generate if needed
        greeting_path = os.path.join(STATIC_AUDIO_DIR, "maia_greeting.wav")
        if not os.path.exists(greeting_path):
            print("🎙️ Generating greeting audio on demand")
            await tts_greeting(filename="maia_greeting.wav")
        
        print("🔊 Playing vibrations")
        client.send_message("/audio/play/sfx/", "vibrations.wav")
        
        await asyncio.sleep(7)
        print("🔊 Playing short.wav")
        client.send_message("/audio/play/music/", "short.wav")

        await asyncio.sleep(10)
        print("🔊 Playing maia_greeting.wav")
        client.send_message("/audio/play/voice/", "maia_greeting.wav")
        
        asyncio.create_task(run_tts_only(filename="maia_output_welcome.wav"))
        
        print("✅ Activation audio sequence completed")
    except Exception as e:
        print(f"⚠️ Error in activation audio sequence: {e}")
