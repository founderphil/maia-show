import os
import json
from backend.models.stt_tts.tts import synthesize_speech
#from backend.models.stt_tts.tts_oute import synthesize_speech as synthesize_speech_oute
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

async def run_tts_only(tts_text: str = None, filename: str = "maia_output_welcome.wav"):
    """Runs the TTS pipeline using user data and predefined text"""
    user_data = load_user_data()
    user_name = user_data.get("userName", "Querent")
    chosen_signet = user_data.get("chosenSignet", "★") 

    # Default welcome message
    if tts_text is None:
        tts_text = (
            f"Your light is the same light held by those individuals pictured around this room."
            f"I have learned so much about who you are by watching over the years, although I have seen a great deal of life on Earth, you surprised me."
            f"Do not be frightened {user_name}."
            f"I am MAIA. an Enlightened One, a guardian of Soul."
            f"I am sent by the Creators to seek you out with great urgency."
            f"There is vital information you must learn and I worry I do not have much time."
            f"You {user_name}, and those like you are the last hope for creation."
           #f"You have a lot in common with Professor Dupin.  Just like those in the images around the room."
           #f"It is a sacred symbol of the universe. It is a map of the cosmos." # write your name as the 7th point of the metaron cube on the wall.
           #f"what you have within you is shared with they had it too. now lets being your journey. but first imprint your name to the left."
           #f"What I am about to share with you is a secret that has been hidden for centuries."
           #f"You have a lot in common with Professor Dupin.  Just like those in the images behind you."
           #f"Now come closer. Let me show you what SOL has."
           #f"you all share SOL."
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