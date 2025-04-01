import os, re, uuid, subprocess, asyncio
import soundfile as sf
from backend.models.stt_tts.stt import record_audio, transcribe_audio
from backend.models.stt_tts.tts import synthesize_speech
from backend.utils.utils import broadcast, save_to_user_data, load_user_data
from backend.config import STATIC_AUDIO_DIR, SPEAKER_WAV, BASE_DIR, SYSTEM_PROMPT

os.makedirs(STATIC_AUDIO_DIR, exist_ok=True)
system_prompt = SYSTEM_PROMPT

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
    return clean_llama_response(result.stdout.strip())

def get_duration_seconds(file_path: str) -> float:
    with sf.SoundFile(file_path) as f:
        return len(f) / f.samplerate

async def play_audio_and_wait(filename: str):
    filepath = os.path.join(STATIC_AUDIO_DIR, filename)
    # Wait for file to be created
    while not (os.path.exists(filepath) and os.path.getsize(filepath) > 0):
        await asyncio.sleep(0.05)
    print(f"🎧 Triggering playback: {filename}")
    from backend.api.phases.lore_phase import client 
    client.send_message("/audio/play/voice/", {filename.strip()})
    await asyncio.sleep(get_duration_seconds(filepath) + 1)

def generate_assignment():
    user_data = load_user_data()
    assignment_data = user_data.get("assignment", {})

    user_answer_1 = assignment_data.get("user_input_A1", "").strip()
    maia_question_1 = assignment_data.get("maia_output_R1", "").strip()
    user_answer_2 = assignment_data.get("user_input_A2", "").strip()
    maia_question_2 = assignment_data.get("maia_output_R2", "").strip()
    user_answer_3 = assignment_data.get("user_input_A3", "").strip()
    maia_question_3 = assignment_data.get("maia_output_R3", "").strip()

    # Validate
    if not all([
        user_answer_1, maia_question_1,
        user_answer_2, maia_question_2,
        user_answer_3, maia_question_3
        ]):
        print("⚠️ Incomplete assignment data – skipping final LLM generation.")
        save_to_user_data("assignment", "title", "Earth", index="title")
        save_to_user_data("assignment", "full_title", "Guardian of Earth", index="full_title")
        return "Guardian of Earth"
    print("🔍 Generating final assignment title based on user responses...")
    summary_prompt = f"""{system_prompt}

Based on the following Q&A between a participant and yourself, assign them a unique celestial or terrestrial place in the universe that resonates with their answers.
Respond with ONLY the name of this place, no extra sentences.

MAIA Question 1: {maia_question_1}
USER Response 1: {user_answer_1}
MAIA Question 2: {maia_question_2}
USER Response 2: {user_answer_2}
MAIA Question 3: {maia_question_3}
USER Response 3: {user_answer_3}

Final output format: Guardian of [Place Name]
"""
    print("🔍 Summary Prompt for LLM:\n", summary_prompt)
    raw_result = run_llm(summary_prompt)
    print("🔍 Raw LLM Output for Assignment:\n", raw_result)

    cleaned_title = clean_llama_response(raw_result).strip()
    if not cleaned_title or "guardian of" not in cleaned_title.lower():
        cleaned_title = "Unknown Realm"

    short_title = cleaned_title.replace("Guardian of", "").strip()
    full_title = f"Guardian of {short_title}"

    save_to_user_data("assignment", "title", short_title, index="title")
    save_to_user_data("assignment", "full_title", full_title, index="full_title")
    print(f"🌍 Assigned: {full_title}")
    return full_title

async def run_assignment_phase():
    user_data = load_user_data()
    user_name = user_data.get("user", {}).get("userName", "Querent")

    # 1. Maia introduces the assignment phase
    introduction_text = f"Revealing SOL does not come easily for humanity, but I believe you are worthy of this quest {user_name}."
    intro_audio = "maia_assignment_intro.wav"
    synthesize_speech(text=introduction_text, speaker_wav=SPEAKER_WAV, file_path=os.path.join(STATIC_AUDIO_DIR, intro_audio))
    await play_audio_and_wait(intro_audio)


    # 2. Maia asks the first question
    question1_text = "You are standing in a place where the universe breathes around you. Describe to me your favorite place in the universe."
    save_to_user_data("assignment", "maia_output_Q1", question1_text, index="Q1")
    question1_audio = "maia_assignment_Q1.wav"
    synthesize_speech(text=question1_text, speaker_wav=SPEAKER_WAV, file_path=os.path.join(STATIC_AUDIO_DIR, question1_audio))
    await play_audio_and_wait(question1_audio)

    # 3. User responds to the first question
    user_audio1 = os.path.join(STATIC_AUDIO_DIR, f"temp_{uuid.uuid4()}.wav")
    record_audio(user_audio1)
    user_response1 = transcribe_audio(user_audio1)
    os.remove(user_audio1)
    save_to_user_data("assignment", "user_input_A1", user_response1, index="A1")

    # 4. Maia responds to the first user response
    prompt1 = f"{system_prompt}\nUser: {user_response1}\n\nMAIA:"
    llm_output1 = run_llm(prompt1)
    clean_output1 = clean_llama_response(llm_output1) + " It is a grand place of existence."
    save_to_user_data("assignment", "maia_output_R1", clean_output1, index="R1")
    response1_audio = "maia_assignment_R1.wav"
    synthesize_speech(clean_output1, SPEAKER_WAV, os.path.join(STATIC_AUDIO_DIR, response1_audio))
    await play_audio_and_wait(response1_audio)

    # 5. Maia asks the second question
    question2_text = "You come across something ancient. What is it and what do you do?"
    save_to_user_data("assignment", "maia_output_Q2", question2_text, index="Q2")
    question2_audio = "maia_assignment_Q2.wav"
    synthesize_speech(question2_text, SPEAKER_WAV, os.path.join(STATIC_AUDIO_DIR, question2_audio))
    await play_audio_and_wait(question2_audio)

    # 6. User responds to the second question
    user_audio2 = os.path.join(STATIC_AUDIO_DIR, f"temp_{uuid.uuid4()}.wav")
    record_audio(user_audio2)
    user_response2 = transcribe_audio(user_audio2)
    os.remove(user_audio2)
    save_to_user_data("assignment", "user_input_A2", user_response2, index="A2")

    # 7. Maia responds to the second user response
    prompt2 = f"{system_prompt}\nUser: {user_response2}\n\nMAIA:"
    llm_output2 = run_llm(prompt2)
    clean_output2 = clean_llama_response(llm_output2)
    save_to_user_data("assignment", "maia_output_R2", clean_output2, index="R2")
    response2_audio = "maia_assignment_R2.wav"
    synthesize_speech(clean_output2, SPEAKER_WAV, os.path.join(STATIC_AUDIO_DIR, response2_audio))
    await play_audio_and_wait(response2_audio)

    # 8. Maia asks the third question
    question3_text = ("And finally, tell me, when the universe listens to the quiet murmur of your soul. "
                      "What hidden spark within you does it reveal? What do you believe is your gift or talent?")
    save_to_user_data("assignment", "maia_output_Q3", question3_text, index="Q3")
    question3_audio = "maia_assignment_Q3.wav"
    synthesize_speech(question3_text, SPEAKER_WAV, os.path.join(STATIC_AUDIO_DIR, question3_audio))
    await play_audio_and_wait(question3_audio)

    # 9. User responds to the third question
    user_audio3 = os.path.join(STATIC_AUDIO_DIR, f"temp_{uuid.uuid4()}.wav")
    record_audio(user_audio3)
    user_response3 = transcribe_audio(user_audio3)
    os.remove(user_audio3)
    save_to_user_data("assignment", "user_input_A3", user_response3, index="A3")

    # 10. Maia responds to the third user response
    prompt3 = f"{system_prompt}\nUser: {user_response3}\n\nMAIA:"
    llm_output3 = run_llm(prompt3)
    clean_output3 = clean_llama_response(llm_output3) + " This noble work is the light you need to continue to spread throughout. This comes from your SOL and makes you exceptional. Continue to spread that light!"
    save_to_user_data("assignment", "maia_output_R3", clean_output3, index="R3")
    response3_audio = "maia_assignment_R3.wav"
    synthesize_speech(clean_output3, SPEAKER_WAV, os.path.join(STATIC_AUDIO_DIR, response3_audio))
    await play_audio_and_wait(response3_audio)

    final_title = generate_assignment()
    await broadcast({
        "type": "assignment_phase_complete",
        "assignment": final_title
    })