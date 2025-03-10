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
from pythonosc.udp_client import SimpleUDPClient

router = APIRouter()

# OSC Client Setup
OSC_IP = "127.0.0.1"
OSC_PORT = 7400
client = SimpleUDPClient(OSC_IP, OSC_PORT)

@router.post("/start_lore")
async def start_lore_phase():
    print("🚀 Starting Phase 3: Lore")

    # Send OSC signal to MAX MSP
    client.send_message("/phase/lore", 1)

    # Simulate a delay for transition
    await asyncio.sleep(1)

    return {"message": "Lore Phase Started"}