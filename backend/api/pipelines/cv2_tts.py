import os
import uuid
import torch
import json
from backend.models.stt_tts.tts import synthesize_speech
from backend.models.vision.vision import capture_webcam_image, detect_vision

# Paths
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
STATIC_AUDIO_DIR = os.path.join(BASE_DIR, "../../static/audio/")
SPEAKER_WAV = os.path.join(BASE_DIR, "../../models/stt_tts/patricia_full.wav")
OUTPUT_FILENAME = "maia_output_seat.wav"
TTS_OUTPUT_PATH = os.path.join(STATIC_AUDIO_DIR, OUTPUT_FILENAME)
USER_DATA_FILE = os.path.join(BASE_DIR, "../../../user_data.json")

os.makedirs(STATIC_AUDIO_DIR, exist_ok=True) #debug. paths are hard.

def load_user_data():
    """Load the user's saved name from user_data.json."""
    try:
        with open(USER_DATA_FILE, "r") as f:
            data = json.load(f)
            return data.get("user", {}).get("userName", "Querent")
    except FileNotFoundError:
        return "Querent"

def run_cv2_tts():
    """Runs facial emotion + posture detection, then generates speech based on it."""
    user_name = load_user_data()
    captured_image_path = capture_webcam_image("captured.png")

    if captured_image_path:
        vision_result = detect_vision(captured_image_path)
    else:
        vision_result = {"emotion": "neutral", "posture": "N/A"}

    emotion = vision_result.get("emotion", "neutral")
    posture = vision_result.get("posture", "unknown")
    print(f"Detected Emotion: {emotion}, Posture: {posture}")

    # Generate dynamic reponse detected emotion & posture
    if posture == "Standing":
        posture_comment = "I see you are standing. Would you like to take a seat and get comfortable?"
    elif posture == "sitting":
        posture_comment = "Ah, you are seated. That means you're ready to listen."
    else:
        posture_comment = "I am unsure if you are standing or sitting, but I sense you are present. PLease, take a seat."

    emotion_comments = {
    "happy": f"You seem happy today, {user_name}. That brings joy to my heart.",
    "sad": f"I sense sadness in you, {user_name}. If you wish to talk, I am here to listen.",
    "neutral": f"I sense a calmness in you, {user_name}. A good place to start.",
    "angry": f"I feel your frustration, {user_name}. Perhaps a deep breath will help clear your mind?",
    "surprised": f"You look shocked! Do not be worried, {user_name}."
}
    
    emotion_comment = emotion_comments.get(emotion, "Your expression intrigues me.")

    # SIT DOWN
    tts_text = (
        f"{user_name}. {emotion_comment} {posture_comment} "
        "There is much we need to discuss." 
        "The world is not how you know it. There is a larger conflict that started before time began."
    )

    print(f"🎙️ Generating speech for: {tts_text}")

    # Generate TTS
    synthesize_speech(
        text=tts_text,
        speaker_wav=SPEAKER_WAV,
        file_path=TTS_OUTPUT_PATH
    )

    print(f"✅ Audio saved to {TTS_OUTPUT_PATH}")

    return {
        "emotion": emotion,
        "posture": posture,
        "transcription": tts_text,
        "llm_response": tts_text,
        "audio_url": f"/static/audio/{OUTPUT_FILENAME}",
    }