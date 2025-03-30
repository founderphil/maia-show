import os, re, uuid, subprocess
from backend.models.stt_tts.stt import record_audio, transcribe_audio
from backend.models.stt_tts.tts import synthesize_speech
from backend.utils.utils import broadcast, save_to_user_data, load_user_data
from backend.config import STATIC_AUDIO_DIR, SPEAKER_WAV, BASE_DIR


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
os.makedirs(STATIC_AUDIO_DIR, exist_ok=True)

def clean_llama_response(output_text: str) -> str:
    output_text = re.sub(r"=+", "", output_text).strip()
    output_text = re.sub(r"Prompt:.*|Generation:.*|Peak memory:.*", "", output_text)
    output_text = re.sub(r"Querent:.*", "", output_text).strip()
    match = re.search(r"MAIA:\s*(.*?)$", output_text, re.DOTALL)
    return match.group(1).strip() if match else output_text

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
    prompt = f"{system_prompt}\nUser: {question_text}\n\nMAIA:"
    llm_output = run_llm(prompt)

    # Append suffix if provided
    if suffix:
        llm_output += " " + suffix

    # Generate speech
    tts_path = os.path.join(STATIC_AUDIO_DIR, output_filename)
    synthesize_speech(text=llm_output, speaker_wav=SPEAKER_WAV, file_path=tts_path)

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
    print("🎤 First question...")
    await handle_question(
        "LORE.USER_INPUT_1",
        "LORE.MAIA_OUTPUT_1",
        "maia_output_question1.wav",
        suffix="What more would you like to know about me or our universe?"
    )

    print("🎤 Second question...")
    user_name = load_user_data().get("userName", "Querent")
    await handle_question(
        "LORE.USER_INPUT_2",
        "LORE.MAIA_OUTPUT_2",
        "maia_output_question2.wav",
        suffix=f"I would like to know you better, {user_name}."
    )