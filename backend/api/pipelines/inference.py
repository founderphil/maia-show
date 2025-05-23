import os
import subprocess
import re
import uuid
import torch
from backend.models.stt_tts.stt import record_audio, transcribe_audio
from backend.models.stt_tts.tts import synthesize_speech
from backend.models.vision.vision import capture_webcam_image, detect_vision
from backend.utils.utils import broadcast, save_to_user_data
from backend.config import STATIC_AUDIO_DIR, SPEAKER_WAV, BASE_DIR, USER_DATA_FILE, STATIC_IMAGE_DIR, SYSTEM_PROMPT
os.makedirs(STATIC_AUDIO_DIR, exist_ok=True)

system_prompt =  SYSTEM_PROMPT
OUTPUT_FILENAME = "maia_output_general.wav"
TTS_OUTPUT_PATH = os.path.join(STATIC_AUDIO_DIR, OUTPUT_FILENAME)
if not os.path.exists(SPEAKER_WAV):
    print(f"⚠️ WARNING: Speaker reference file missing at {SPEAKER_WAV}.")

def clean_llama_response(output_text: str) -> str:
    output_text = re.sub(r"=+", "", output_text).strip()
    output_text = re.sub(r"Prompt:.*|Generation:.*|Peak memory:.*", "", output_text)
    output_text = re.sub(r"Querent:.*", "", output_text).strip()
    match = re.search(r"MAIA:\s*(.*?)$", output_text, re.DOTALL)
    if match:
        output_text = match.group(1).strip()
    return output_text

async def run_cv2stt_llm_tts():
    """Runs the full inference pipeline (Vision + STT + LLM + TTS)."""
    audio_id = str(uuid.uuid4())
    audio_file = os.path.join(STATIC_AUDIO_DIR, f"temp_{audio_id}.wav")

    record_audio(audio_file, max_duration=None)
    user_question = transcribe_audio(audio_file)
    print("User said:", user_question)

    
    captured_image_path = os.path.join(STATIC_IMAGE_DIR, "captured.png")
    if captured_image_path:
        vision_result = detect_vision(captured_image_path)
    else:
        vision_result = {"emotion": "Neutral", "posture": "N/A"}
    print("User emotion:", vision_result["emotion"])
    print("User posture:", vision_result["posture"])
    
    final_prompt = f"{system_prompt}\nUser emotion: {vision_result['emotion']}.\nUser posture: {vision_result['posture']}.\nUser: {user_question}?\n\nMAIA:"
    print("Final Prompt:", final_prompt)
    
    model_path = os.path.join(BASE_DIR, "backend/models/llm/llama3_mlx")
    adapter_path = os.path.join(BASE_DIR, "backend/models/llm/adapters")

    print("Running LLaMA MLX inference...")
    result = subprocess.run([
        "mlx_lm.generate",
        "--model", model_path,
        "--adapter-path", adapter_path,
        "--prompt", final_prompt,
        "--max-tokens", "128"
    ], capture_output=True, text=True)

    print("🔍 Raw LLaMA Output (stdout):\n", result.stdout) #DEBUG
    print("🔍 Raw LLaMA Errors (stderr):\n", result.stderr) #DEBUG

    output_text = result.stdout.strip()
    llm_response = clean_llama_response(output_text)

    if not llm_response.strip():
        llm_response = "I'm sorry, I didn't understand that. Can you try again?"

    print("Cleaned MAIA Response:", llm_response)

    print("Saving TTS audio...")
    
    print("Saving TTS audio...")
    synthesize_speech(
        text=llm_response,
        speaker_wav=SPEAKER_WAV,  
        file_path=TTS_OUTPUT_PATH
    )

    print(f"✅ TTS Output Saved at {TTS_OUTPUT_PATH}")

    ws_message = {
        "type": "full_inference",
        "user_question": user_question,
        "final_prompt": final_prompt,
        "llm_response": llm_response,
        "audio_url": f"/static/audio/{OUTPUT_FILENAME}",
        "vision_image": "/static/captured.png",
        "vision_emotion": vision_result.get("emotion", "N/A"),
        "vision_posture": vision_result.get("posture", "N/A"),
    }
    # First broadcast call is sufficient
    # await broadcast(ws_message) 

    if ws_message is None:
        print("🚨 ERROR: WebSocket message is None!")
    else:
        print("📡 Sending WebSocket Message:", ws_message)

    # Redundant broadcast removed
    # try:
    #     broadcast(ws_message)
    # except Exception as e:
    #     print(f"⚠️ WebSocket Broadcast Error: {e}")

    save_to_user_data("intro", "user", user_question)
    save_to_user_data("intro", "maia", llm_response)

    os.remove(audio_file)

    return ws_message
