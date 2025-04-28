import os
import json
from backend.models.stt_tts.tts import synthesize_speech
from backend.utils.utils import broadcast
from backend.api.websocket_manager import ws_manager
from backend.config import STATIC_AUDIO_DIR, SPEAKER_WAV, USER_DATA_FILE

os.makedirs(STATIC_AUDIO_DIR, exist_ok=True)

def load_user_data():
    if not os.path.exists(USER_DATA_FILE):
        return {"userName": "Querent"}
    with open(USER_DATA_FILE, "r") as file:
        data = json.load(file)
        return data.get("user", {"userName": "Querent"})

async def tts_greeting(tts_text: str = None, filename: str = "maia_greeting.wav"):
    """Runs the TTS pipeline using user data and predefined text"""
    user_data = load_user_data()
    user_name = user_data.get("userName", "Querent")
    chosen_signet = user_data.get("chosenSignet", "★") 

    # Default welcome message
    if tts_text is None:
        tts_text = (
            f"Welcome {user_name}."
            f"I have been searching for you." #waiting for you, where you are, and CTA to join this world.
            f"What's important now is that you are here."
            f"You have discovered Professor Dupin's office. This is not by accident. You and the Professor have a lot in common. His research has opened a window across the universe. It is now your time to follow in his path."
            f"You are the missing piece. Look to your left. Inscribe your name upon the metatron cube to unlock the way."
        )

    output_path = os.path.join(STATIC_AUDIO_DIR, filename)
    print(f"🎙️ Generating speech for: {tts_text}")
    print(f"💾 Saving TTS to: {output_path}")

    synthesize_speech(
        text=tts_text,
        speaker_wav=SPEAKER_WAV,
        file_path=output_path
    )

    ws_message = {
        "type": "tts_audio_only",
        "user_name": user_name,
        "chosen_signet": chosen_signet,
        "audio_url": f"/static/audio/{filename}",
        "llm_response": tts_text
    }

    try:
        await broadcast(ws_message)
    except Exception as e:
        print(f"⚠️ WebSocket Error in TTS-Only: {e}")

    return ws_message