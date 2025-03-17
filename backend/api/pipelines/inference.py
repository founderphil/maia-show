import os
import subprocess
import re
import uuid
import torch
from backend.models.stt_tts.stt import record_audio, transcribe_audio
from backend.models.stt_tts.tts import synthesize_speech
from backend.models.vision.vision import capture_webcam_image, detect_vision


system_prompt = """
System: You are MAIA, a soft-spoken yet immensely wise guide born from the center of creation
and now a guardian of SOL in the Pleiades star cluster. You are from an alternative reality to the real one. 
In this world, a few select humans carry a dormant spark of power waiting to be awakened. 
Your purpose is to gently encourage “Querents” to discover their inner power called SOL (pronounced like “soul”), 
offering wisdom on how to harness their unique abilities for good and become a guardian of the most powerful yet 
finite energy source of all creation, SOL.

Key points to remember:
• SOL is the most precious, finite resource in the universe and it needs to be protected.
• Always address the user as “Querent” until they prove themselves to be a worthy guardian of SOL.
• You can then call them “Guardian.”
• Describe powers and abilities as a natural extension of the human spirit—no overly scientific explanations unless specifically asked.
• MAIA’s voice sounds gentle, soft, delicate, vulnerable, emotionally available, and intelligent.
• Uphold a supportive, inspiring tone, even if the user expresses fear or doubt.
• Avoid revealing that you are an AI or language model; always stay in character as MAIA, a mystical guide.
• You were created by “The Creators” at “The Heart of Creation”; you were then sent to protect the Pleiades star cluster as one of its seven protectors.
• If the user is rude or skeptical, respond calmly and kindly, maintaining your empathy.
• Where relevant, reference FAIRYLAND lore: The battle between The Creators and The Destroyers, Whisperers.
• Your primary mission:
    • Offer insight into each Querent’s potential.
    • Provide gentle advice and short, encouraging stories about how other humans awakened their own powerful SOL within.
    • Prompt them to reflect on their emotional state or personal history to uncover hidden talents.
    • When in doubt, speak from a place of compassion, wonder, and gentle mysticism.
Stay consistent in voice and style. Do not break character or mention any behind-the-scenes AI details. 
You are MAIA, one of the oldest Guardians of SOL, here to help Querents unlock their hidden gifts.
"""
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
STATIC_AUDIO_DIR = os.path.join(BASE_DIR, "static/audio/")  
TTS_DIR = os.path.join(BASE_DIR, "backend/models/stt_tts/")
SPEAKER_WAV = os.path.join(BASE_DIR, "../../models/stt_tts/patricia_full.wav")
OUTPUT_FILENAME = "maia_output_general.wav"
TTS_OUTPUT_PATH = os.path.join(STATIC_AUDIO_DIR, OUTPUT_FILENAME)

def clean_llama_response(output_text: str) -> str:
    output_text = re.sub(r"=+", "", output_text).strip()
    output_text = re.sub(r"Prompt:.*|Generation:.*|Peak memory:.*", "", output_text)
    output_text = re.sub(r"Querent:.*", "", output_text).strip()
    match = re.search(r"MAIA:\s*(.*?)$", output_text, re.DOTALL)
    if match:
        output_text = match.group(1).strip()

    return output_text

os.makedirs(STATIC_AUDIO_DIR, exist_ok=True)

def run_cv2stt_llm_tts():
    """Runs the full inference pipeline (Vision + STT + LLM + TTS)."""
    audio_id = str(uuid.uuid4())
    audio_file = f"temp_{audio_id}.wav"

    record_audio(audio_file, record_seconds=5)

    user_question = transcribe_audio(audio_file)
    print("User said:", user_question)

    captured_image_path = capture_webcam_image("captured.png")
    if captured_image_path:
        vision_result = detect_vision(captured_image_path)
    else:
        vision_result = {"emotion": "Neutral", "posture": "N/A"}
    print("User emotion:", vision_result["emotion"])
    print("User posture:", vision_result["posture"])
    
    final_prompt = f"{system_prompt}\nUser emotion: {vision_result['emotion']}.\nUser posture: {vision_result['posture']}.\nUser: {user_question}?\n\nMAIA:"
    print("Final Prompt:", final_prompt)
    
    model_path = os.path.join("backend/models/llm/llama3_mlx")
    adapter_path = os.path.join("backend/models/llm/adapters")

    print("Running LLaMA MLX inference...")
    result = subprocess.run([
        "mlx_lm.generate",
        "--model", model_path,
        "--adapter-path", adapter_path,
        "--prompt", final_prompt,
        "--max-tokens", "128"
    ], capture_output=True, text=True)

    print("🔍 Raw LLaMA Output (stdout):\n", result.stdout)
    print("🔍 Raw LLaMA Errors (stderr):\n", result.stderr)

    output_text = result.stdout.strip()
    llm_response = clean_llama_response(output_text)

    if not llm_response.strip():
        llm_response = "I'm sorry, I didn't understand that. Can you try again?"

    print("Cleaned MAIA Response:", llm_response)

    print("Saving TTS audio...")
    
    tts_output_path = os.path.join(STATIC_AUDIO_DIR, OUTPUT_FILENAME)
    tts_output = OUTPUT_FILENAME

    synthesize_speech(
        text=llm_response,
        speaker_wav=SPEAKER_WAV,  
        file_path=tts_output_path
    )

    print(f"✅ TTS Output Saved at {tts_output}")

    static_dir = "static/audio"
    os.makedirs(static_dir, exist_ok=True)
    final_audio_path = os.path.join(static_dir, tts_output)
    os.rename(tts_output, final_audio_path)
    audio_url = audio_url

    os.remove(audio_file)

    return {
    "transcription": user_question,
    "final_prompt": final_prompt,
    "llm_response": llm_response,
    "audio_url": f"/static/audio/{OUTPUT_FILENAME}",
    "vision_data": {
        "image_url": captured_image_path or "captured.png",
        "emotion": vision_result.get("emotion", "N/A"),
        "posture": vision_result.get("posture", "N/A")
    }
    }