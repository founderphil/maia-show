"""
Phase 3 - LORE
19. Light cue 3
        MAIA LED - addressable : color gold. set brightness to wav file’s audio frequency spectrum height using MAX MSP.
        HOUSE LIGHT 1 : 10%
        HOUSE LIGHT 2 : 10%
        CHAIR SPOT : ON 50%
        MAIA SPOT 1 : ON 80%
        MAIA SPOT 2 : ON 80%
        MAIA PROJECTOR 1 : ON 100%
        MAIA PROJECTOR 2 : ON 100%
        AUTOPLAY AUDIO IN MAX MSP. MAIA_LORE.WAV
20. IF MAIA_LORE.WAV is not playing, START “TTS_only” Pipeline
    -“So I come to you <profile_data.name> and ask you to carry the torch that was passed on from generation to generation and take up the great responsibility to be a guardian of SOL. Before you take up this higher calling. What questions do you have for me, Querent?”
    -AUTOPLAY audio in MAX MSP patched to MAIA Led Brightness
21. Light cue 4:
        MAIA LED - addressable : color gold. set brightness to wav file’s audio frequency spectrum height using MAX MSP. flicker 40% of leds to a purple color.
        HOUSE LIGHT 1 : 10%
        HOUSE LIGHT 2 : 10%
        CHAIR SPOT : ON 50%
        MAIA SPOT 1 : FADE IN to 100% over 10000ms
        MAIA SPOT 2 : FADE IN to 100% over 10000ms
        MAIA PROJECTOR 1 : OFF
        MAIA PROJECTOR 2 : OFF
21. START “CV2STT_LLM_TTS” Pipeline.
    -Send STORY PROMPT + “end with do you have another question?”
    -Save user response as, lore.user_input_1 to localDB 
    -Save AI output text as, lore.MAIA_OUTPUT_1.
    -AUTOPLAY lore.MAIA_OUTPUT_2 (MAX MSP). 
    -AUTOPLAY anything_else.wav


"""

from fastapi import APIRouter
import asyncio
import os
import json
from pythonosc.udp_client import SimpleUDPClient
from backend.api.pipelines.tts_only import run_tts_only
from backend.api.pipelines.question_llm_tts import run_question_sequence
from backend.utils.utils import save_to_user_data, broadcast
from backend.config import BASE_DIR, USER_DATA_FILE

router = APIRouter()

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
    client.send_message("/audio/play/", "patricia_temp_edit.wav")

    #await asyncio.sleep(60)  # let MAIA_LORE.wav play

    user_data = load_user_data()
    user_name = user_data.get("userName", "Querent")

    # Scripted welcome TTS
    tts_text = (
        f"And now that battle to protect the last remnants of SOL comes to you. "
        f"I come to you {user_name} and ask you to protect the light. "
        f"A guardianship, passed on from The Enlightened Ones. "
        f"Before you take up this higher calling. What questions do you have for me, {user_name}?"
    )

    tts_result = await run_tts_only(tts_text=tts_text, filename="maia_lore_question_intro.wav")
    save_to_user_data("lore", "maia", tts_result["llm_response"])

    client.send_message("/audio/play", ["/static/audio/maia_lore_intro.wav", 1.0])

    await broadcast({
        "type": "phase_lore",
        "phase": "lore",
        "message": "Phase 3 - Lore Started",
        "llm_response": tts_text,
        "audio_url": "/static/audio/maia_lore_intro.wav"
    })

    await asyncio.sleep(8)  # let TTS audio play before questions begin

    # Interactive Q&A sequence
    print("✨ Entering Lore Q&A Phase")
    await run_question_sequence()

    return {"message": "Phase 3 - Lore Phase with Q&A Completed"}