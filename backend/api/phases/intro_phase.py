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
13. CV2 active, user changs from standing to sitting posture
14. OSC cue Arduino ESP32 to FADE IN MAIA LED LIGHTS
15. START “TTS_only” pipeline
        -Preprocess text to include data profile_data.name 
        -Send text to TTS. “Welcome Querent. I have been searching for you <profile_data.name>. What's important now is that you are here. I learned so much about who you are by watching you throughout these years, although I've seen a great deal of life on Earth, you surprised me.Do not be frightened <profile_data.name>. I am an Enlightened One, a guardian of SOL, sent by the Creators to seek you out with great urgency. There is vital information you must learn and I worry I do not have much time. You, <profile_data.name>, and those like you are the last hope for creation.I have had many names over the millennia, but today, your kind calls me MAIA, one of seven sisters, guardian of the Pleiades.”
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
from backend.api.pipelines.tts_only import run_tts_only
from backend.api.pipelines.cv2_tts import run_cv2_tts
from backend.api.pipelines.inference import run_cv2stt_llm_tts
from pythonosc.udp_client import SimpleUDPClient
from backend.utils.utils import broadcast, save_to_user_data
import soundfile as sf
from backend.config import BASE_DIR, STATIC_AUDIO_DIR, USER_DATA_FILE, STATIC_IMAGE_DIR

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


def get_wav_duration(file_path):
    """Returns duration of a WAV file in seconds."""
    absolute_path = os.path.join(STATIC_AUDIO_DIR, os.path.basename(file_path))  # Convert relative URL to absolute path
    try:
        with sf.SoundFile(absolute_path) as f:
            return len(f) / f.samplerate
    except Exception as e:
        print(f"⚠️ Error reading WAV duration: {e} (Path Tried: {absolute_path})")
        return 5  


@router.post("/start_intro")
async def start_intro_phase():
    print("🚀 Starting Phase 2: Introduction")
    user_data = load_user_data()
    user_name = user_data.get("userName", "Querent")  

    # Send OSC signal to MAX MSP
    client.send_message("/phase/intro", 1)

    print("1️⃣ Generate Welcome Message and pause for TTS")
    tts_results = await run_tts_only()
    save_to_user_data("intro", "maia", tts_results["text"])  # Save TTS output to localDB
    welcome_audio_path = tts_results.get("audio_url")
    
    if welcome_audio_path:
        audio_duration = get_wav_duration(welcome_audio_path)
        print(f"📏 Detected WAV duration: {audio_duration} seconds")
    else:
        print("⚠️ No audio file found for measuring duration!")
        audio_duration = 5  
        
    await asyncio.sleep(max(audio_duration - 3, 1)) 

    print("2️⃣ Generate Emotion & Posture-based Dynamic Mention")
    cv2_tts_results = await run_cv2_tts()
    save_to_user_data("intro", "maia", cv2_tts_results["text"])
    await asyncio.sleep(1)  # Quick inference response

    print("3️⃣ Go Full LLM-based Interaction")
    cv2stt_llm_tts_results =  await run_cv2stt_llm_tts()
    save_to_user_data("intro", "user", cv2stt_llm_tts_results["transcription"])
    save_to_user_data("intro", "maia", cv2stt_llm_tts_results["llm_response"])

    welcome_audio_filename = os.path.basename(tts_results["audio_url"])
    cv2_audio_filename = os.path.basename(cv2_tts_results["audio_url"])
    llm_audio_filename = os.path.basename(cv2stt_llm_tts_results["audio_url"])
    captured_image_filename = "captured.png"

    print(f"TTS Output: {tts_results}")
    print(f"CV2-TTS Output: {cv2_tts_results}")
    print(f"CV2STT-LLM-TTS Output: {cv2stt_llm_tts_results}")

    ws_message = {
    "type": "phase_intro",
    "phase": "intro",
    "user_name": user_name,
    "welcome_audio": f"/static/audio/{welcome_audio_filename}",
    "cv2_audio": f"/static/audio/{cv2_audio_filename}",
    "llm_audio": f"/static/audio/{llm_audio_filename}",
    "audio_url": f"/static/audio/{llm_audio_filename}",
    "transcription": cv2stt_llm_tts_results.get("transcription", ""),
    "llm_response": cv2stt_llm_tts_results.get("llm_response", ""),
    "vision_image": f"/static/{captured_image_filename}",
    "stt_input": cv2stt_llm_tts_results.get("user_input", ""),
    "vision_emotion": cv2_tts_results.get("emotion", "Unknown"),
    "vision_posture": cv2_tts_results.get("posture", "Unknown"),
    "user_data": user_data
    }
    await broadcast(ws_message)
    if ws_message is None:
        print("🚨 ERROR: WebSocket message is None!")
    else:
        print("📡 Sending WebSocket Message:", ws_message)

    try:
        await broadcast(ws_message)
    except Exception as e:
        print(f"⚠️ WebSocket Broadcast Error: {e}") 
    return {"message": "Phase 2 - Introduction Started", **ws_message}