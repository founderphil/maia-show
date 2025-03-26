"""
Phase 2 - INTRODUCTION
12. Light cue 2
        MAIA LED - addressable : set brightness to wav file’s audio frequency spectrum height using MAX MSP.
        HOUSE LIGHT 1 : 10%
        HOUSE LIGHT 2 : 10%
        CHAIR SPOT : ON 100%, then FADE to 50% over 10000ms
        MAIA SPOT 1 : FADE IN to 100% over 10000ms
        MAIA SPOT 2 : FADE IN to 100% over 10000ms
        MAIA PROJECTOR 1 : OFF
        MAIA PROJECTOR 2 : OFF
13. Play music MAJO.WAV at 25% volume & MAIA VOICE WELCOME WAV FILE at 100% volume
14. CV2 active, user changs from standing to sitting posture
16. START  “CV2_to_LLM_to_TTS” Pipeline
        -STORY PROMPT + “This Querent currently looks <vision_data.emotion>. Comfort them that you are a safe, if needed. Comment on their appearance in the nicest calmest way possible. Put them at ease. Ask them, “What is your initial question?””
        -Save AI output text as, intro.maia_output_1 to localDB.
        -display intro.maia_output_1.(WaveSurfer)
        -Send intro.maia_output_1 to MAX MSP.
        -AUTOPLAY audio in MAX MSP patched to MAIA Led Brightness
17. START “CV2STT_LLM_TTS” Pipeline.
        -Save user response as, intro.user_input_1 to localDB 
        -Save AI output text as, INTRO.MAIA_OUTPUT_2.
        -AUTOPLAY INTRO.MAIA_OUTPUT_2 (MAX MSP). 
18.START “CV2_TTS” pipeline
        -IF VISION_DATA.POSTURE != sitting, send prompt “Please take a seat. The world is not how you know it. There is a larger conflict that started before time began.”, else, “Please remain seated. The world is not how you know it. There is a larger conflict that started before time began.
        -AUTOPLAY INTRO.MAIA_OUTPUT_2 (WaveSurfer). 
"""

import os
import json
import asyncio
from fastapi import APIRouter
from backend.api.pipelines.cv2_tts import run_cv2_tts
from backend.api.pipelines.inference import run_cv2stt_llm_tts
from pythonosc.udp_client import SimpleUDPClient
from backend.utils.utils import broadcast, save_to_user_data
from backend.config import BASE_DIR, USER_DATA_FILE

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
    client.send_message("/audio/play/music/", "soundtrack")
    client.send_message("/audio/play/voice/", "maia_output_welcome.wav")
    await asyncio.sleep(1)

    #16. CV2 active, user changs from standing to sitting posture
    print("1️⃣ Generate Emotion & Posture-based Dynamic Mention")
    cv2_tts_results = await run_cv2_tts()
    save_to_user_data("intro", "maia", cv2_tts_results["llm_response"])
    await asyncio.sleep(1)

    print("2️⃣ Go Full LLM-based Interaction")
    cv2stt_llm_tts_results = await run_cv2stt_llm_tts()
    save_to_user_data("intro", "user", cv2stt_llm_tts_results["transcription"])
    save_to_user_data("intro", "maia", cv2stt_llm_tts_results["llm_response"])

    cv2_audio_filename = os.path.basename(cv2_tts_results["audio_url"])
    llm_audio_filename = os.path.basename(cv2stt_llm_tts_results["audio_url"])
    captured_image_filename = "captured.png"

    print(f"CV2-TTS Output: {cv2_tts_results}")
    print(f"CV2STT-LLM-TTS Output: {cv2stt_llm_tts_results}")

    ws_message = {
        "type": "phase_intro",
        "phase": "intro",
        "message": "Phase 2 - Intro Started",
        "user_name": user_name,
        "cv2_audio": f"/static/audio/{cv2_audio_filename}",
        "llm_audio": f"/static/audio/{llm_audio_filename}",
        "audio_url": f"/static/audio/{llm_audio_filename}",
        "transcription": cv2stt_llm_tts_results.get("user_question", ""),
        "llm_response": cv2stt_llm_tts_results.get("llm_response", ""),
        "vision_image": f"/static/{captured_image_filename}",
        "vision_emotion": cv2_tts_results.get("emotion", "Unknown"),
        "vision_posture": cv2_tts_results.get("posture", "Unknown"),
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

    return {"message": "Phase 2 - Introduction Started", **ws_message}