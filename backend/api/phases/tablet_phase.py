import asyncio, json, os
from fastapi import APIRouter
from backend.api.pipelines.tts_only import run_tts_only
from backend.api.pipelines.greetings_tts import tts_greeting
from backend.models.stt_tts.tts import TTSModel
from backend.api.websocket_manager import ws_manager
from backend.utils.utils import osc_client
from backend.config import USER_DATA_FILE, STATIC_AUDIO_DIR
import soundfile as sf
from backend.api.phases.intro_phase import start_intro_phase

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

def send_chosen_color_osc():
    try:
        with open(USER_DATA_FILE, "r") as f:
            user_data = json.load(f)
        chosen_color = user_data["user"]["chosenColor"]
        osc_client.send_message("/user/chosenColor/", chosen_color)
        print(f"✅ Sent chosenColor via OSC: {chosen_color}")
    except Exception as e:
        print(f"⚠️ Error sending chosenColor via OSC: {e}")

## THIS IS RESET POSITION
@router.post("/reset_room") 
async def reset_room():
    global _tts_started, _tts_generation_in_progress, _greeting_generated, _welcome_generated
    
    print("ROOM RESET")
    
    _tts_started = False
    _tts_generation_in_progress = False
    _greeting_generated = False
    _welcome_generated = False

    # Preload TTS model for the show
    print("🔄 Preloading TTS model for show...")
    TTSModel.get_instance()
    print("✅ TTS model loaded and ready.")
    
######## RESET LIGHTS
    await asyncio.sleep(1)
    print("Go Cue 1 - Lights, Reset Tablet, Play Music")
    lighting_cues = {
        "maiaLEDmode": 0,  #mode 0 is off
        "floor": 1,
        "desk": 0, #0 is on
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


_tts_generation_in_progress = False
_greeting_generated = False
_welcome_generated = False
_tts_started = False 


@router.post("/run_tablet_tts")
async def run_tablet_tts():
    global _tts_started
    print("🔊 Starting TTS 'Continue' button")

    if _tts_started:
        print("⚠️ TTS generation already started, skipping")
        return {"message": "TTS generation already in progress"}
    _tts_started = True

    print("🎙️ [run_tablet_tts] Generating greeting TTS only")
    await tts_greeting(filename="maia_greeting.wav")
    print("✅ [run_tablet_tts] Greeting TTS generated")

    return {"message": "Greeting TTS generation completed"}


@router.post("/activate")
async def activate():
    print("✨ [ACTIVATE] User pressed Activate! (should run immediately, not wait for TTS)")
    send_chosen_color_osc()
    print("✨ send color")
    # Start playing audio IMMEDIATELY
    print("🔊 Playing vibrations.wav")
    osc_client.send_message("/audio/volume/", -20) #turn down MUSIC track
    osc_client.send_message("/audio/play/sfx/", "vibrations.wav")
    osc_client.send_message("/lighting/desk", 1) #off
    await asyncio.sleep(0.5)
    osc_client.send_message("/lighting/desk", 0) #on
    await asyncio.sleep(0.25)
    osc_client.send_message("/lighting/desk", 1)
    await asyncio.sleep(0.35)
    osc_client.send_message("/lighting/desk", 0)
    await asyncio.sleep(0.1)
    osc_client.send_message("/lighting/desk", 1)
    

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

    # This task runs in the background and should NOT block the response
    asyncio.create_task(continue_activation_audio_sequence())

    print("✅ Activation audio sequence started")
    return {"success": True, "message": "Activation successful"}


def generate_missing_audio_files():
    global _tts_started

    if _tts_started:
        print("⚠️ TTS generation already started")
        return
    _tts_started = True

    print("🎙️ Starting TTS generation for both greeting and welcome (main process, sequentially)")
    async def sequential_tts():
        await tts_greeting(filename="maia_greeting.wav")
        await run_tts_only(filename="maia_output_welcome.wav")
    asyncio.create_task(sequential_tts())

async def continue_activation_audio_sequence():
    try:
        greeting_path = os.path.join(STATIC_AUDIO_DIR, "maia_greeting.wav")
        welcome_path = os.path.join(STATIC_AUDIO_DIR, "maia_output_welcome.wav")

        # Play vibration and transition music immediately
        print("🔊 Playing short.wav")
        osc_client.send_message("/audio/volume/", -15)
        osc_client.send_message("/audio/play/music/", "short.wav")

        # Wait for maia_greeting.wav to be ready
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

        # Wait for maia_greeting.wav to finish before playing greeting.wav
        greeting_duration = 5
        greeting_path = os.path.join(STATIC_AUDIO_DIR, "maia_greeting.wav")
        if os.path.exists(greeting_path):
            greeting_duration = get_wav_duration(greeting_path)
            print(f"ℹ️ maia_greeting.wav duration: {greeting_duration:.1f}s")
        await asyncio.sleep(greeting_duration)

        print("🔊 Playing greeting.wav")
        osc_client.send_message("/audio/play/voice/", "greeting.wav")

        # Start generating welcome audio in the background as soon as greeting starts playing
        asyncio.create_task(run_tts_only(filename="maia_output_welcome.wav"))

        # Wait for greeting.wav to finish, then play welcome as soon as it's ready
        greeting2_duration = 5
        greeting2_path = os.path.join(STATIC_AUDIO_DIR, "greeting.wav")
        if os.path.exists(greeting2_path):
            greeting2_duration = get_wav_duration(greeting2_path)
            print(f"ℹ️ greeting.wav duration: {greeting2_duration:.1f}s")
        await asyncio.sleep(greeting2_duration)

        asyncio.create_task(queue_welcome_audio())

        print("✅ Initial activation audio sequence completed")
    except Exception as e:
        print(f"⚠️ Error in activation audio sequence: {e}")

async def queue_welcome_audio():
    try:
        welcome_path = os.path.join(STATIC_AUDIO_DIR, "maia_output_welcome.wav")

        # Wait for welcome audio to be ready, then play immediately
        timeout = 0
        max_wait = 60
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

        print(" Waiting for welcome audio file to be fully written...")
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

        # Play welcome audio immediately
        print("🔊 Playing maia_output_welcome.wav")
        osc_client.send_message("/audio/play/voice/", "maia_output_welcome.wav")
        print("✅ Welcome audio played successfully")

        # Start the intro phase after welcome audio is played
        asyncio.create_task(start_intro_phase())
    except Exception as e:
        print(f"⚠️ Error queuing welcome audio: {e}")
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
        
        # Start the intro phase after welcome audio is played
        asyncio.create_task(start_intro_phase())
    except Exception as e:
        print(f"⚠️ Error queuing welcome audio: {e}")
