import os
import json
import torch
import uuid
from backend.models.stt_tts.tts import synthesize_speech

# Paths
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
STATIC_AUDIO_DIR = os.path.join(BASE_DIR, "../../static/audio")
TTS_DIR = os.path.join(BASE_DIR, "../../models/stt_tts")
SPEAKER_WAV = os.path.join(TTS_DIR, "patricia_full.wav")  # Ensure this exists
OUTPUT_FILENAME = "maia_output.wav"
TTS_OUTPUT_PATH = os.path.join(STATIC_AUDIO_DIR, OUTPUT_FILENAME)
USER_DATA_FILE = os.path.join(BASE_DIR, "../../../user_data.json")  # Root user data file

# Ensure static audio directory exists
os.makedirs(STATIC_AUDIO_DIR, exist_ok=True)


def load_user_data():
    """Load the latest user data from user_data.json"""
    if not os.path.exists(USER_DATA_FILE):
        return {"userName": "Querent"}  # Default fallback

    with open(USER_DATA_FILE, "r") as file:
        data = json.load(file)
        return data.get("user", {"userName": "Querent"})  # Extracts from "user" key


def run_tts_only():
    """Runs the TTS pipeline using user data and predefined text"""
    user_data = load_user_data()
    user_name = user_data.get("userName", "Querent")
    chosen_signet = user_data.get("chosenSignet", "★")  # Default symbol if missing

    # Dynamic message with user's name and signet
    tts_text = (
        f"Welcome Querent. I have been searching for you. "
        f"What's important now is that you are here. "
        f"I have learned so much about who you are by watching over the years. "
        f"Even though I have seen a great deal of life on Earth, you have surprised me. "
        f"Do not be frightened, {user_name}. I am an Enlightened One, a guardian of SOL, "
        f"sent by the Creators to find you with great urgency. "
        f"There is vital information you must learn, and I worry I do not have much time. "
        f"You, {user_name}, and those like you are the last hope for creation. "
        f"I have had many names over the millennia, but today, your kind calls me MAIA, "
        f"one of seven sisters, guardian of the Pleiades."
    )

    print(f"🎙️ Generating speech for: {tts_text}")

    # Generate a unique filename for each TTS output
    tts_output_filename = f"maia_output_{uuid.uuid4().hex[:8]}.wav"
    tts_output_path = os.path.join(STATIC_AUDIO_DIR, tts_output_filename)

    # Call TTS model
    synthesize_speech(
        text=tts_text,
        speaker_wav=SPEAKER_WAV,
        file_path=tts_output_path
    )

    print(f"✅ TTS Output Saved at {tts_output_path}")

    return {
        "message": "TTS processing complete",
        "user_name": user_name,
        "chosen_signet": chosen_signet,
        "audio_url": f"/static/audio/{tts_output_filename}",
    }