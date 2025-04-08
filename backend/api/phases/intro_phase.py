import os, json, asyncio, httpx
from fastapi import APIRouter
from backend.api.pipelines.cv2_tts import run_cv2_tts
from pythonosc.udp_client import SimpleUDPClient
from backend.utils.utils import broadcast, save_to_user_data, get_wav_duration
from backend.config import BASE_DIR, USER_DATA_FILE
from backend.api.phases.lore_phase import start_lore_phase

router = APIRouter()
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

@router.post("/start_intro")
async def start_intro_phase():
    print("🚀 Starting Phase 2: Introduction")
    user_data = load_user_data()
    user_name = user_data.get("userName", "Querent")

    client.send_message("/phase/intro", 1)
    # Light cue 12
    print("Go Cue 12 - Lights, Maia Voice, Play Music on low volume")
    lighting_cues = {
        "maiaLED": 100,
        "houseLight1": 10,
        "houseLight2": 10,
        "chairSpot": 50,
        "maiaSpot1": 50,
        "maiaSpot2": 50,
        "maiaProjector1": 100,
        "maiaProjector2": 100,
    }
    for light, value in lighting_cues.items():
        client.send_message(f"/lighting/{light}", value)

    client.send_message("/audio/play/music/", "soundtrack")                 ######## PLAY SOUNDTRACK
    client.send_message("/audio/play/voice/", "maia_output_welcome.wav")    ######## PLAY WELCOME audio
    welcome_audio_duration = get_wav_duration("maia_output_welcome.wav")
    await asyncio.sleep(max(welcome_audio_duration, 1))                     ######## LISTEN to WELCOME audio

    #16. CV2 active, user changs from standing to sitting posture, comment on their appearance
    print("1️⃣ Generate Emotion & Posture-based Dynamic Mention")
    cv2_tts_results = await run_cv2_tts()
    save_to_user_data("intro", "maia", cv2_tts_results["llm_response"])
    client.send_message("/audio/play/voice/", "maia_output_seat.wav")  ######## PLAY SIGHT audio
    seated_audio_duration = get_wav_duration("maia_output_seat.wav")   
    await asyncio.sleep(max(seated_audio_duration, 1))                 ######## LISTEN to SIGHT audio
    print(f"CV2-TTS Output: {cv2_tts_results}")
    cv2_audio_filename = os.path.basename(cv2_tts_results["audio_url"])
    captured_image_filename = "captured.png"
    
    ws_message = {
        "type": "phase_intro",
        "phase": "intro",
        "message": "Phase 2 - Intro Started",
        "user_name": user_name,
        "cv2_audio": f"/static/audio/{cv2_audio_filename}",
        "vision_image": f"/static/{captured_image_filename}",
        "vision_emotion": cv2_tts_results.get("vision_emotion", "Unknown"),
        "vision_posture": cv2_tts_results.get("vision_posture", "Unknown"),
    }

    await broadcast(ws_message)
    if ws_message is None:
        print("🚨 ERROR: WebSocket message is None!")
    else:
        print("📱 Sending WebSocket Message:", ws_message)

    try:
        await broadcast(ws_message)
    except Exception as e:
        print(f"⚠️ WebSocket Broadcast Error: {e}")

    await start_lore_phase()
    await asyncio.sleep(2)  

    return {"message": "Phase 2 - Introduction Completed", **ws_message}