import asyncio, json, os, multiprocessing, sys
from fastapi import APIRouter
from backend.api.pipelines.tts_only import run_tts_only
from backend.api.pipelines.greetings_tts import tts_greeting
from backend.api.websocket_manager import ws_manager
from backend.utils.utils import broadcast, save_to_user_data, osc_client
from backend.config import USER_DATA_FILE, STATIC_AUDIO_DIR
import soundfile as sf

os.makedirs(STATIC_AUDIO_DIR, exist_ok=True)

router = APIRouter()

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
    global _tts_started, _tts_generation_in_progress, _greeting_generated, _welcome_generated
    
    print("ROOM RESET")
    
    _tts_started = False
    _tts_generation_in_progress = False
    _greeting_generated = False
    _welcome_generated = False
    
######## RESET LIGHTS
    await asyncio.sleep(1)
    print("Go Cue 1 - Lights, Reset Tablet, Play Music")
    lighting_cues = {
        "maiaLED": 0, # 0-255
        "floor": 1,
        "desk": 1,
        "projector": 0,
    }
    for light, value in lighting_cues.items():
        osc_client.send_message(f"/lighting/{light}", value) 
    await asyncio.sleep(1)
######## RESET MUSIC
    osc_client.send_message("/audio/volume/", -5)
    await asyncio.sleep(1)
    osc_client.send_message("/audio/play/music/", "instrumental.wav") 
    print("Room reset complete")
    return {"message": "Room Reset"}

@router.post("/start_tablet")
async def start_tablet_phase():
    """Start the tablet phase and begin TTS generation in the background"""
    global _tts_started
    
    print("🚀 Starting Show!")
    
    if _tts_started:
        print("⚠️ TTS generation already started, skipping")
        return {"message": "Tablet Phase Started (TTS already in progress)"}
    _tts_started = True
    
    print("🎙️ Starting TTS generation for all audio files")
    process = multiprocessing.Process(
        target=run_tts_in_process,
        args=(True, True)  
    )
    process.daemon = True
    process.start()
    
    return {"message": "Tablet Phase Started"}

def run_tts_in_process(generate_greeting=True, generate_welcome=True):

    sys.path.append("/Users/phil/github/maia-show")
    
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    
    # Run TTS - welcome and greeting
    try:
        from backend.api.pipelines.tts_only import run_tts_only
        from backend.api.pipelines.greetings_tts import tts_greeting
        from backend.config import STATIC_AUDIO_DIR
        os.makedirs(STATIC_AUDIO_DIR, exist_ok=True)

        # Generate greeting 
        if generate_greeting:
            print("🎙️ Process: Generating greeting audio")
            greeting_result = loop.run_until_complete(tts_greeting(filename="maia_greeting.wav"))
            print("✅ Process: Greeting audio generated")
        
        # Generate welcome
        if generate_welcome:
            print("🎙️ Process: Generating welcome audio")
            welcome_result = loop.run_until_complete(run_tts_only(filename="maia_output_welcome.wav"))
            print("✅ Process: Welcome audio generated")
    except Exception as e:
        print(f"⚠️ Process: Error generating audio: {e}")
    finally:
        loop.close()

_tts_generation_in_progress = False
_greeting_generated = False
_welcome_generated = False
_tts_started = False 

@router.post("/run_tablet_tts")
async def run_tablet_tts():
    global _tts_started
    
    print("🔊 Starting TTS generation asynchronously from 'Continue' button")
    
    if _tts_started:
        print("⚠️ TTS generation already started, skipping")
        return {"message": "TTS generation already in progress"}
    _tts_started = True
    
    print("🎙️ Starting background TTS generation - this will take ~35 seconds but won't block the UI")
    process = multiprocessing.Process(
        target=run_tts_in_process,
        args=(True, True) 
    )
    process.daemon = True
    process.start()

    return {"message": "TTS generation started in background process"}


@router.post("/activate")
async def activate():
    print("✨ User pressed Activate!")
    
    # Start playing audio IMMEDIATELY
    print("🔊 Playing vibrations.wav immediately")
    osc_client.send_message("/audio/volume/", -20) #turn down MUSIC track
    osc_client.send_message("/audio/play/sfx/", "vibrations.wav")
    
    ws_message = {
        "type": "activation_success",
        "phase": "tablet",
        "message": "Activation successful"
    }
    
    try:
        print("📡 Sending WebSocket Message:", ws_message)
        await ws_manager.broadcast(ws_message)
        phase_message = {
            "type": "phase_tablet",
            "phase": "tablet",
            "message": "Phase 1 - Tablet Started"
        }
        await ws_manager.broadcast(phase_message)
    except Exception as e:
        print(f"⚠️ WebSocket Broadcast Error: {e}")
    
    asyncio.create_task(continue_activation_audio_sequence())
    
    return {"success": True, "message": "Activation successful"}


def generate_missing_audio_files():
    global _tts_started
    
    if _tts_started:
        print("⚠️ TTS generation already started")
        return
    _tts_started = True
    
    print("🎙️ Starting TTS generation for both greeting and welcome")
    process = multiprocessing.Process(
        target=run_tts_in_process,
        args=(True, True)
    )
    process.daemon = True
    process.start()

async def continue_activation_audio_sequence():
    try:
        greeting_path = os.path.join(STATIC_AUDIO_DIR, "maia_greeting.wav")
        welcome_path = os.path.join(STATIC_AUDIO_DIR, "maia_output_welcome.wav")
        
        if not os.path.exists(greeting_path) or not os.path.exists(welcome_path):
            if not _tts_started:
                print("⚠️ TTS not started yet, starting it now during activation")
                generate_missing_audio_files()
            else:
                print("ℹ️ TTS generation already in progress, waiting for files to be created")
        
        await asyncio.sleep(7)
        print("🔊 Playing short.wav")
        osc_client.send_message("/audio/volume/", -15)
        osc_client.send_message("/audio/play/music/", "short.wav")
        
        await asyncio.sleep(3)
        
        greeting_path = os.path.join(STATIC_AUDIO_DIR, "maia_greeting.wav")
        timeout = 0
        max_wait = 40
        
        while not os.path.exists(greeting_path) and timeout < max_wait:
            print(f"⏳ Waiting for greeting audio to be generated... ({timeout}/{max_wait}s)")
            await asyncio.sleep(1)
            timeout += 1
        
        if not os.path.exists(greeting_path):
            print("⚠️ Greeting audio not generated in time, continuing to wait...")
            while not os.path.exists(greeting_path):
                await asyncio.sleep(1)
                timeout += 1
                if timeout % 5 == 0:  
                    print(f"⏳ Still waiting for greeting audio... ({timeout}s)")
        
        print("🔊 Playing maia_greeting.wav")
        osc_client.send_message("/audio/play/voice/", "maia_greeting.wav")

        asyncio.create_task(queue_welcome_audio())
        
        print("✅ Initial activation audio sequence completed")
    except Exception as e:
        print(f"⚠️ Error in activation audio sequence: {e}")

async def queue_welcome_audio():
    try:
        greeting_path = os.path.join(STATIC_AUDIO_DIR, "maia_greeting.wav")
        greeting_duration = 5
        
        if os.path.exists(greeting_path):
            greeting_duration = get_wav_duration(greeting_path)
            print(f"ℹ️ Greeting duration: {greeting_duration:.1f}s")
        
        wait_time = max(greeting_duration - 1, 0)
        print(f"⏱️ Waiting {wait_time:.1f}s for greeting to finish")
        await asyncio.sleep(wait_time)
        
        welcome_path = os.path.join(STATIC_AUDIO_DIR, "maia_output_welcome.wav")
        timeout = 0
        max_wait = 40
    
        while not os.path.exists(welcome_path) and timeout < max_wait:
            print(f"⏳ Waiting for welcome audio file to be created... ({timeout}/{max_wait}s)")
            await asyncio.sleep(1)
            timeout += 1
        
        if not os.path.exists(welcome_path):
            print("⚠️ Welcome audio not generated in time, continuing to wait...")
            while not os.path.exists(welcome_path):
                await asyncio.sleep(1)
                timeout += 1
                if timeout % 5 == 0: 
                    print(f"⏳ Still waiting for welcome audio file to be created... ({timeout}s)")
        
        print("📊 Waiting for welcome audio file to be fully written...")
        last_size = -1
        stable_count = 0
        while stable_count < 2:
            try:
                current_size = os.path.getsize(welcome_path)
                if current_size == last_size:
                    stable_count += 1
                    print(f"📊 File size stable ({stable_count}/3): {current_size} bytes")
                else:
                    stable_count = 0
                    print(f"📊 File size changed: {last_size} -> {current_size} bytes")
                last_size = current_size
                await asyncio.sleep(1)
            except Exception as e:
                print(f"⚠️ Error checking file size: {e}")
                await asyncio.sleep(1)
        
        print("📊 File size stable, waiting 1 more second to ensure file is fully written")
        await asyncio.sleep(1)
        
        # Play welcome audio
        print("🔊 Playing maia_output_welcome.wav")
        osc_client.send_message("/audio/play/voice/", "maia_output_welcome.wav")
        print("✅ Welcome audio played successfully")
    except Exception as e:
        print(f"⚠️ Error queuing welcome audio: {e}")
