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
from fastapi import APIRouter
from pythonosc.udp_client import SimpleUDPClient

router = APIRouter()

OSC_IP = "127.0.0.1"
OSC_PORT = 7400
client = SimpleUDPClient(OSC_IP, OSC_PORT)