"""
Phase 4 - ASSIGNMENT (a quiz where querents are deemed worthy to become a guardian)
22. Light cue 5:
        MAIA LED - addressable : color gold. set brightness to wav file’s audio frequency spectrum height using MAX MSP. flicker 40% of leds to a purple color.
        HOUSE LIGHT 1 : 10%
        HOUSE LIGHT 2 : 10%
        CHAIR SPOT : ON 50%
        MAIA SPOT 1 : FADE IN to 100% over 10000ms
        MAIA SPOT 2 : FADE IN to 100% over 10000ms
        MAIA PROJECTOR 1 : OFF
        MAIA PROJECTOR 2 : OFF
23. START “CV2STT_LLM_TTS” Pipeline.
    -Send STORY PROMPT
    -Save user response as, lore.user_input_2 to localDB 
    -Save AI output text as, lore.MAIA_OUTPUT_2.
    -AUTOPLAY lore.MAIA_OUTPUT_2 (MAX MSP)
23. START “TTS_only” pipeline
    -Preprocess text to include data profile_data.name 
    -Send text to TTS. “I would like to know you better. Revealing SOL does not come easily for humanity, but I believe you are worthy of this quest You are standing in a place where the universe breathes around you. <profile_data.name>, Describe to me your favorite place in the universe.”
25. START “CV2STT_LLM_TTS” Pipeline.
    -Send STORY PROMPT
    -Save user response as, assignment.user_input_1 to localDB 
    -Save AI output text as, assignment.MAIA_OUTPUT_1.
    -AUTOPLAY assignment.MAIA_OUTPUT_1 (MAX MSP).
27. START “ASSIGNMENT” pipeline. 
    -Process assignment.user_input_1 for major themes
    -Save major themes in text string, assignment.themes_1
28. START “TTS_only” pipeline
    -Preprocess text to include data profile_data.name 
    -Send text to TTS. “You come across something ancient. What is it and what do you do?”
29.START “CV2STT_LLM_TTS” Pipeline.
    -Send STORY PROMPT
    -Save user response as, assignment.user_input_2 to localDB 
    -Save AI output text as, assignment.MAIA_OUTPUT_2.
    -AUTOPLAY assignment.MAIA_OUTPUT_2 (MAX MSP).
30. START “ASSIGNMENT” pipeline. 
    -Process assignment.user_input_2 for major themes
    -Save major themes in text string, assignment.themes_2
    31.START “TTS_only” pipeline
    -Preprocess text to include data profile_data.name 
    -Send text to TTS. “And finally, tell me, when the universe listens to the quiet murmur of your soul. What hidden spark within you does it reveal? What do you believe is your gift or talent?”
32.START “CV2STT_LLM_TTS” Pipeline.
    -Send STORY PROMPT
    -Save user response as, assignment.user_input_2 to localDB 
    -Save AI output text as, assignment.MAIA_OUTPUT_3.
    -AUTOPLAY assignment.MAIA_OUTPUT_3 (MAX MSP).
33. START “ASSIGNMENT” pipeline. 
    -Process assignment.user_input_2 for major themes
    -Save major themes in text string, assignment.themes_3
    -START “TTS_only” pipeline
    -Preprocess text to include data profile_data.name 
    -Send text to TTS. “This noble work is the light you need to continue to spread throughout. This comes from your SOL and makes you exceptional. Continue to spread that light!”
"""

from fastapi import APIRouter
import asyncio
from pythonosc.udp_client import SimpleUDPClient

router = APIRouter()

# OSC Client Setup
OSC_IP = "127.0.0.1"
OSC_PORT = 7400
client = SimpleUDPClient(OSC_IP, OSC_PORT)

@router.post("/start_assign")
async def start_assign_phase():
    """Handles the Assign phase transition."""
    print("📜 Starting Phase 4: Assignment")

    # Send OSC signal to MAX MSP
    client.send_message("/phase/asign", 1)

    # Simulate a delay for transition
    await asyncio.sleep(1)

    return {"message": "Assignment Phase Started"}