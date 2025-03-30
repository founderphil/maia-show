import os
import json
from backend.models.stt_tts.tts import synthesize_speech
from backend.utils.utils import broadcast
from backend.api.websocket_manager import ws_manager
from backend.config import STATIC_AUDIO_DIR, SPEAKER_WAV, USER_DATA_FILE

OUTPUT_FILENAME = "maia_output_welcome.wav"
TTS_OUTPUT_PATH = os.path.join(STATIC_AUDIO_DIR, OUTPUT_FILENAME)
os.makedirs(STATIC_AUDIO_DIR, exist_ok=True)


def load_user_data():
    """Load the latest user data from user_data.json"""
    if not os.path.exists(USER_DATA_FILE):
        return {"userName": "Querent"} 

    with open(USER_DATA_FILE, "r") as file:
        data = json.load(file)
        return data.get("user", {"userName": "Querent"}) 

async def run_tts_only(tts_text: str = None, filename: str = OUTPUT_FILENAME):
    """Runs the TTS pipeline using user data and predefined text"""
    user_data = load_user_data()
    user_name = user_data.get("userName", "Querent")
    chosen_signet = user_data.get("chosenSignet", "★") 
    if tts_text is None:

        tts_text = (
            f"Welcome {user_name}."
            f"I have been searching for you."
            f"What's important now is that you are here."
            f"I have learned so much about who you are by watching over the years, although I have seen a great deal of life on Earth, you surprised me."
            f"Do not be frightened {user_name}."
            f"I am MAIA. an Enlightened One, a guardian of Soul." #actually SOL but trying to help the TTS. 
            f"I am sent by the Creators to seek you out with great urgency."
            f"There is vital information you must learn and I worry I do not have much time."
            f"You {user_name}, and those like you are the last hope for creation."
        )

    print(f"🎙️ Generating speech for: {tts_text}")

    synthesize_speech(
        text=tts_text,
        speaker_wav=SPEAKER_WAV,
        file_path=TTS_OUTPUT_PATH
    )

    print(f"TTS Output Saved at {TTS_OUTPUT_PATH}")

    ws_message = {
        "type": "tts_audio_only",
        "user_name": user_name or "Unknown",   
        "chosen_signet": chosen_signet or "?",
        "audio_url": f"/static/audio/{OUTPUT_FILENAME}",
        "llm_response": tts_text
    }

    if ws_message is None:
        print("🚨 ERROR: WebSocket message is None!")
    else:
        print("📡 Sending WebSocket Message:", ws_message)

    try:
        await broadcast(ws_message)
    except Exception as e:
        print(f"⚠️ WebSocket Error in TTS-Only: {e}")
    return ws_message