import os, re, uuid, subprocess, re, asyncio
from backend.models.stt_tts.stt import record_audio, transcribe_audio
from backend.models.stt_tts.tts import synthesize_speech
from backend.utils.utils import broadcast, save_to_user_data, load_user_data, get_wav_duration
from backend.config import STATIC_AUDIO_DIR, SPEAKER_WAV, BASE_DIR, SYSTEM_PROMPT
from pythonosc.udp_client import SimpleUDPClient

# OSC Client Setup
OSC_IP = "127.0.0.1"
OSC_PORT = 7400
client = SimpleUDPClient(OSC_IP, OSC_PORT)

system_prompt = SYSTEM_PROMPT

os.makedirs(STATIC_AUDIO_DIR, exist_ok=True)


def clean_llama_response(output_text: str) -> str:
    parts = output_text.split("==========")
    if len(parts) > 1:
        answer_text = parts[1].strip()
    else:
        answer_text = output_text.strip()
    sentences = re.split(r'(?<=[.!?])\s+', answer_text)
    
    limited_output = ' '.join(sentences[:2])
    
    return limited_output

def run_llm(prompt: str) -> str:
    model_path = os.path.join(BASE_DIR, "backend/models/llm/llama3_mlx")
    adapter_path = os.path.join(BASE_DIR, "backend/models/llm/adapters")

    result = subprocess.run([
        "mlx_lm.generate",
        "--model", model_path,
        "--adapter-path", adapter_path,
        "--prompt", prompt,
        "--max-tokens", "128"
    ], capture_output=True, text=True)

    print("🔍 LLM stdout:", result.stdout)
    print("🔍 LLM stderr:", result.stderr)

    return clean_llama_response(result.stdout.strip())

async def handle_question(question_key: str, response_key: str, output_filename: str, suffix: str = ""):
    # Record + transcribe
    audio_path = os.path.join(STATIC_AUDIO_DIR, f"{uuid.uuid4()}.wav")
    record_audio(audio_path)
    question_text = transcribe_audio(audio_path)

    # Run LLM
    print(f"🔍 LLM Input: {question_text}")
    prompt = f"{system_prompt}\nUser Question to you that you should answer: {question_text}\n\nMAIA:"
    llm_output = run_llm(prompt)

    # Append suffix if provided
    if suffix:
        llm_output += " " + suffix

    # Generate speech
    tts_path = os.path.join(STATIC_AUDIO_DIR, output_filename)
    synthesize_speech(text=llm_output, speaker_wav=SPEAKER_WAV, file_path=tts_path)

    # Get audio duration
    audio_duration = get_wav_duration(tts_path)
    print(f"🔊 Audio Duration: {audio_duration} seconds")
    await asyncio.sleep(audio_duration)

    # Play audio
    print("🔊 Playing audio...")
    client.send_message("/audio/play/voice/", output_filename)
    
    # Save to user_data
    save_to_user_data("lore", "user", question_text)
    save_to_user_data("lore", "maia", llm_output)

    # Broadcast WebSocket
    await broadcast({
        "type": "full_inference",
        "user_question": question_text,
        "final_prompt": prompt,
        "llm_response": llm_output,
        "audio_url": f"/static/audio/{output_filename}",
        "vision_image": "/static/captured.png"
    })

    os.remove(audio_path)
    return question_text, llm_output

async def run_question_sequence():
    print("🎤 First participant question...")
    await handle_question(
        "LORE.USER_INPUT_1",
        "LORE.MAIA_OUTPUT_1",
        "maia_output_question1.wav",
        suffix="What more would you like to know about me or our universe?"
    )

    print("🎤 Second participant question...")
    user_name = load_user_data().get("userName", "Querent")
    await handle_question(
        "LORE.USER_INPUT_2",
        "LORE.MAIA_OUTPUT_2",
        "maia_output_question2.wav",
        suffix=f"I would like to know you better, {user_name}."
    )