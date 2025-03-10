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

import asyncio
import json
from fastapi import APIRouter
from backend.api.pipelines.inference import run_cv2stt_llm_tts
from backend.api.pipelines.tts_only import  run_tts_only
from backend.utils.utils import clients, osc_client, broadcast, ws_manager

router = APIRouter()

@router.post("/start_intro")
async def start_intro_phase():
    """Handles the introduction phase, triggering AI inference."""
    print("🚀 Starting Phase 2: Introduction")

    # Send OSC signal to MAX MSP
    osc_client.send_message("/phase/intro", 1)

    # Notify frontend via WebSocket
    await ws_manager.broadcast({
        "type": "phase_update",
        "phase": "intro",
        "lighting": {
            "maiaLED": 100,
            "houseLight1": 50,
            "houseLight2": 50
        },
        "audio": {
            "voiceover": {"file": "intro_voice.wav", "volume": 1.0}
        }
    })

    #welcome
    ai_results = run_tts_only()
    # Run AI Pipeline
    #ai_results = run_cv2stt_llm_tts()

    # Send TTS audio to frontend
    await broadcast({
        "type": "tts_audio",
        "audio_url": ai_results["audio_url"],
        "transcription": ai_results["transcription"],
        "llm_response": ai_results["llm_response"]
    })

    return {"message": "Introduction Phase Started", **ai_results}


async def broadcast(message: dict):
    """Broadcasts messages via WebSocket."""
    for client in clients:
        try:
            await client.send_text(json.dumps(message))
        except Exception:
            clients.remove(client)