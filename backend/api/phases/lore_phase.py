from fastapi import APIRouter
import asyncio, os, json
from asyncio import Event
from pythonosc.udp_client import SimpleUDPClient
from backend.api.pipelines.tts_only import run_tts_only
from backend.api.pipelines.question_llm_tts import run_question_sequence
from backend.utils.utils import save_to_user_data, broadcast, get_wav_duration
from backend.config import BASE_DIR, USER_DATA_FILE, STATIC_AUDIO_DIR

router = APIRouter()
audio_done_event = Event()

# OSC Client Setup
OSC_IP = "127.0.0.1"
OSC_PORT = 7400
client = SimpleUDPClient(OSC_IP, OSC_PORT)

def load_user_data():
    """Load the latest user data from `user_data.json`."""
    user_data_path = os.path.join(BASE_DIR, USER_DATA_FILE)
    if os.path.exists(user_data_path):
        with open(user_data_path, "r") as f:
            return json.load(f).get("user", {})
    return {}

@router.post("/start_lore")
async def start_lore_phase():
    print("🚀 Starting Phase 3: Lore")

    # Cue lights/audio in MAX MSP
    client.send_message("/phase/lore", 1)

    print("Play Lore Movie!")
    client.send_message("/video/play/", "Maia_Lore_cut.mp4")
    patricia_path = os.path.join(STATIC_AUDIO_DIR, "Lore_Audio.wav")
    lore_duration = get_wav_duration(patricia_path)
    print("🔊 Playing THE LORE STORY VIDEO in MAX MSP, next generate inference...")

    user_data = load_user_data()
    user_name = user_data.get("userName", "Querent")

    # Scripted welcome TTS
    scripted_text = (
        f"And now that battle to protect the last remnants of SOL comes to you. "
        f"I come to you {user_name} and ask you to protect the light. "
        f"A guardianship, passed on from The Enlightened Ones. "
        f"Before you take up this higher calling. What questions do you have for me, {user_name}?"
    )

    tts_result = await run_tts_only(tts_text=scripted_text, filename="maia_lore_Q_intro.wav")
    save_to_user_data("lore", "maia", tts_result["llm_response"])
    print("⏳ Waiting for MAX MSP to finish playing intro...")
    await asyncio.sleep(66)
    #audio_done_event.clear()
    #try:
    #    await asyncio.wait_for(audio_done_event.wait(), timeout=lore_duration)
    #except asyncio.TimeoutError:
    #    print("⚠️ Timeout waiting for MAX MSP. Proceeding anyway.")
    #await asyncio.sleep(lore_duration)
    client.send_message("/audio/play/voice/", "maia_lore_Q_intro.wav")
    await asyncio.sleep(22)
    

    await broadcast({
        "type": "phase_lore",
        "phase": "lore",
        "message": "Phase 3 - Lore Started",
        "llm_response": scripted_text,
        "audio_url": "/static/audio/maia_lore_Q_intro.wav"
    })

    # Interactive Q&A sequence
    print("✨ Entering Lore Q&A Phase")
    await run_question_sequence()

    client.send_message("/audio/play/voice/", "maia_lore_Q_outro.wav")
    return {"message": "Phase 3 - Lore Phase with Q&A Completed"}