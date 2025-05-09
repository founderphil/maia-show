import os
import json
import asyncio
from backend.models.stt_tts.tts import synthesize_speech
from backend.models.vision.vision import capture_webcam_image, detect_vision
from backend.config import STATIC_AUDIO_DIR, SPEAKER_WAV, USER_DATA_FILE, STATIC_IMAGE_DIR

os.makedirs(STATIC_AUDIO_DIR, exist_ok=True)

OUTPUT_FILENAME = "maia_output_seat.wav"
TTS_OUTPUT_PATH = os.path.join(STATIC_AUDIO_DIR, OUTPUT_FILENAME)

def load_user_data():
    """Load the user's saved name from user_data.json."""
    try:
        with open(USER_DATA_FILE, "r") as f:
            data = json.load(f)
            return data.get("user", {}).get("userName", "Querent")
    except FileNotFoundError:
        return "Querent"

async def run_cv2_tts():
    """Runs facial emotion + posture detection, then generates speech based on it."""
    user_name = load_user_data()

    captured_image_path = capture_webcam_image(os.path.join(STATIC_IMAGE_DIR, "captured.png"))

    if captured_image_path:
        vision_result = detect_vision(captured_image_path)
    else:
        vision_result = {"emotion": "neutral", "posture": "N/A"}

    #emotion and posture snapshot
    emotion = vision_result.get("emotion", "neutral")
    posture = vision_result.get("posture", "unknown")
    print(f"👁️ Detected Emotion: {emotion}, Posture: {posture}")

    posture_comments = {
        "Sitting": "Ah, you are seated. Remain comfortable.",
        "Standing":  "I see you are standing. Would you like to take a seat and get comfortable?",
    }
    posture_comment = posture_comments.get(posture, "I am unsure if you are standing or sitting, but I sense you are present. Please, take a seat.")

    emotion_comments = {
    "happy": f"You appear happy today, {user_name}. That brings joy to my heart.",
    "sad": f"I sense sadness in you, {user_name}. I am here to listen and find your light.",
    "neutral": f"I sense a calmness in you, {user_name}. A good place to start.",
    "angry": f"I feel your frustration, {user_name}. Perhaps a deep breath will help clear your mind?",
    "surprised": f"You look shocked! Do not be worried, {user_name}."
}

    emotion_comment = emotion_comments.get(emotion, "Your expression intrigues me.")

    # SIT DOWN
    tts_text = (
       f"{emotion_comment} {posture_comment} "
        f"There is much we need to discuss."
        f"The world is not how you know it. There is a larger conflict that started before time began."

    #    if i need to generate python3 -m backend.api.pipelines.cv2_tts
    #    f"Welcome Querent, I am Maia. Guardian of soul."
    #    f"You have uncovered a portal to a world of creation and destruction."
    #    f"Before the first breath of time, there was only Creation."
    #    f"A force beyond form, a radiant harmony, birthing light, birthing life. And within all life, the Seed of Creation was placed."
    #    f"it is the source of all things, SOL. For an eternity, Creation flourished, untouched by shadow. Until the Destroyers beheld the light."
    #    f"Their hunger to claim dominion over all existence sparked an endless war across the universe between creation and destruction."
    #    f"We, guardians of Creation, The Enlightened Ones, resisted. The Whisperers, agents of the Destroyers, sought to destroy the light but the light endured."
    #    f"For as long as SOL burns within humanity, the battle for creation will never be lost. And now that battle to protect the last remnants of SOL comes to you"
    )

    print(f"🎙️ Generating speech for: {tts_text}")

    # Generate TTS
    synthesize_speech(
        text=tts_text,
        speaker_wav=SPEAKER_WAV,
        file_path=TTS_OUTPUT_PATH
    )

    print(f"✅ Audio saved to {TTS_OUTPUT_PATH}")

    ws_message = {
    "type": "vision_update",
    "vision_image": "/static/captured.png",
    "vision_emotion": emotion,
    "vision_posture": posture,
    "audio_url": f"/static/audio/{OUTPUT_FILENAME}",
    "llm_response": tts_text,
    }

    if ws_message is None:
        print("🚨 ERROR: WebSocket message is None!")
    else:
        print("📡 Sending WebSocket Message:", ws_message)

    return ws_message

if __name__ == "__main__":
    asyncio.run(run_cv2_tts())
