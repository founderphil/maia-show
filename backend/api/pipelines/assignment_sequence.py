import os, re, uuid, subprocess, asyncio
import soundfile as sf
from backend.models.stt_tts.stt import record_audio, transcribe_audio
from backend.models.stt_tts.tts import synthesize_speech
from backend.utils.utils import broadcast, save_to_user_data, load_user_data, osc_client
from backend.config import STATIC_AUDIO_DIR, SPEAKER_WAV, BASE_DIR, SYSTEM_PROMPT

os.makedirs(STATIC_AUDIO_DIR, exist_ok=True)
system_prompt = SYSTEM_PROMPT

def clean_llama_response(output_text: str) -> str:

    parts = output_text.split("==========")
    if len(parts) > 1:
        answer_text = parts[1].strip()
    else:
        answer_text = output_text.strip()
    answer_text = re.sub(r"Prompt:.*|Generation:.*|Peak memory:.*", "", answer_text, flags=re.DOTALL)
    if not answer_text.strip():
        return "I sense your energy and connection to the universe. Your journey with SOL is just beginning."
    sentences = re.split(r'(?<=[.!?])\s+', answer_text)
    limited_output = ' '.join(sentences[:2])
    limited_output = re.sub(r"^(User:|MAIA:)\s*", "", limited_output)
    
    return limited_output.strip()

def run_llm(prompt: str, max_tokens: int = 128, temperature: float = 0.0) -> str:
    model_path = os.path.join(BASE_DIR, "backend/models/llm/llama3_mlx")
    adapter_path = os.path.join(BASE_DIR, "backend/models/llm/adapters")
    result = subprocess.run([
    "mlx_lm.generate",
    "--model", model_path,
    "--adapter-path", adapter_path,
    "--prompt", prompt,
    "--max-tokens", str(max_tokens),
    "--temp", str(temperature),
    "--top-p", "1.0"
    ], capture_output=True, text=True)
    print("🔍 LLM stdout:", result.stdout)
    print("🔍 LLM stderr:", result.stderr) 
    return clean_llama_response(result.stdout.strip())

def get_duration_seconds(file_path: str) -> float:
    with sf.SoundFile(file_path) as f:
        return len(f) / f.samplerate

async def play_audio_and_wait(filename: str):
    filepath = os.path.join(STATIC_AUDIO_DIR, filename)

    while not (os.path.exists(filepath) and os.path.getsize(filepath) > 0):
        await asyncio.sleep(0.05)
    print(f"🎧 Triggering playback: {filename}")
    osc_client.send_message("/audio/play/voice/", {filename.strip()})
    await asyncio.sleep(get_duration_seconds(filepath) + 0.5)
    

def generate_assignment():
    user_data = load_user_data()
    

    user_answer_1 = user_data.get("user", {}).get("assignment.maia_output_A1", "").strip()
    maia_response_1 = user_data.get("user", {}).get("assignment.maia_output_R1", "").strip()
    user_answer_2 = user_data.get("user", {}).get("assignment.maia_output_A2", "").strip()
    maia_response_2 = user_data.get("user", {}).get("assignment.maia_output_R2", "").strip()
    user_answer_3 = user_data.get("user", {}).get("assignment.maia_output_A3", "").strip()
    maia_response_3 = user_data.get("user", {}).get("assignment.maia_output_R3", "").strip()
    maia_question_1 = user_data.get("user", {}).get("assignment.maia_output_Q1", "").strip()
    maia_question_2 = user_data.get("user", {}).get("assignment.maia_output_Q2", "").strip()
    maia_question_3 = user_data.get("user", {}).get("assignment.maia_output_Q3", "").strip()

    # Debug print
    print(f"User data for assignment generation:")
    print(f"Q1: {maia_question_1}")
    print(f"A1: {user_answer_1}")
    print(f"R1: {maia_response_1}")
    print(f"Q2: {maia_question_2}")
    print(f"A2: {user_answer_2}")
    print(f"R2: {maia_response_2}")
    print(f"Q3: {maia_question_3}")
    print(f"A3: {user_answer_3}")
    print(f"R3: {maia_response_3}")

    # Validate
    if not all([
        user_answer_1, maia_response_1,
        user_answer_2, maia_response_2,
        user_answer_3, maia_response_3
        ]):
        print("⚠️ Incomplete assignment data – skipping final LLM generation.")
        save_to_user_data("assignment", "title", "Earth", index="title")
        save_to_user_data("assignment", "full_title", "Guardian of Earth", index="full_title")
        return "Guardian of Earth"
    print("🔍 Generating final assignment title based on user responses...")
    
    summary_prompt = f"""SYSTEM: You are a location assignment system. Your ONLY task is to output a single location name based on user responses. DO NOT output any instructions, explanations, or additional text.

TASK: Based on the user's answers to three questions, assign ONE specific location (on Earth or in space) that resonates with their responses. The location will be a place they are assigned to protect.

INPUT:
Question 1: "{maia_question_1}"
Answer 1: "{user_answer_1}"
Question 2: "{maia_question_2}"
Answer 2: "{user_answer_2}"
Question 3: "{maia_question_3}"
Answer 3: "{user_answer_3}"

EXAMPLES OF VALID OUTPUTS (EXACTLY AS SHOWN):
Andromeda
Pacific Ocean
Great Pyramid of Giza
Mount Everest
Amazon Rainforest
Sahara Desert
Milky Way
Caribbean Sea
Library of Alexandria
Northern Lights
Great Barrier Reef
Himalayas
Mariana Trench
Stonehenge
Atlantis
Mount Olympus
Grand Canyon
Machu Picchu
Serengeti Plains
Arctic Circle

EXAMPLES OF INVALID OUTPUTS (DO NOT USE THESE):
- "The user should be assigned to protect the Caribbean Sea"
- "I assign the user to the Pacific Ocean"
- "Based on the user's answers, the location is Mount Everest"
- "The location name is Andromeda"
- "Assignment: Milky Way"
- "Guardian of the Amazon Rainforest"

RULES:
1. Output ONLY the name of the location - nothing else
2. Choose a location that connects to themes in the user's answers
3. The location can be on Earth or in space
4. Do not include any explanations or additional text
5. Do not use the word "Assignment" or any other label
6. Do not include quotes around your answer
7. Do not include any punctuation
8. Do not include any instructions or meta-commentary

YOUR RESPONSE (LOCATION NAME ONLY, NO OTHER TEXT):
"""
    print("🔍 Summary Prompt for LLM:\n", summary_prompt)

    raw_result = run_llm(summary_prompt, max_tokens=24, temperature=1.0)
    print("🔍 Raw LLM Output for Assignment:\n", raw_result)

    # Clean the output of the assignment is different than the Q&A session
    cleaned_title = raw_result.strip()
    if "==========" in cleaned_title:
        parts = cleaned_title.split("==========")
        if len(parts) > 1:
            cleaned_title = parts[1].strip()
    cleaned_title = re.sub(r"Prompt:.*|Generation:.*|Peak memory:.*", "", cleaned_title, flags=re.DOTALL)
    cleaned_title = cleaned_title.replace('"', '').replace("'", "").replace(".", "").strip()
    prefixes_to_remove = [
        "the ", "a ", "an ", "guardian of ", "guardian ", "place: ", "place name: ", 
        "location: ", "location name: ", "assignment: ", "output: ", "response: "
    ]
    for prefix in prefixes_to_remove:
        if cleaned_title.lower().startswith(prefix):
            cleaned_title = cleaned_title[len(prefix):].strip()
    if "\n" in cleaned_title:
        lines = [line.strip() for line in cleaned_title.split("\n") if line.strip()]
        if lines:
            cleaned_title = lines[0]

    invalid_patterns = [
        "user should", "respond with", "assignment", "guardian of", "creator", 
        "light of", "sol", "querent", "your response", "output", "location name",
        "place name", "answer", "choose", "select", "pick", "assign", "protect"
    ]
    
    is_invalid = (
        not cleaned_title or 
        "[" in cleaned_title.lower() or 
        len(cleaned_title) > 30 or
        len(cleaned_title.split()) > 4 or #MAX WORDS FOR ASSIGNMENT
        any(pattern in cleaned_title.lower() for pattern in invalid_patterns)
    )
    
    if is_invalid:
        print("⚠️ Invalid place name generated, using fallback")
        
        if any(term in user_answer_1.lower() for term in ["caribbean", "shore", "beach", "ocean", "sea", "water", "wave"]):
            if "caribbean" in user_answer_1.lower():
                cleaned_title = "Caribbean Sea"
            else:
                water_fallbacks = ["Caribbean Sea", "Pacific Ocean", "Atlantic Ocean", "Great Barrier Reef"]
                import random
                cleaned_title = random.choice(water_fallbacks)
        elif any(term in user_answer_2.lower() for term in ["book", "read", "language", "knowledge", "wisdom", "ancient"]):
            knowledge_fallbacks = ["Library of Alexandria", "Celestial Library", "Ancient Archives"]
            import random
            cleaned_title = random.choice(knowledge_fallbacks)
        elif any(term in user_answer_3.lower() for term in ["light", "good", "see", "vision", "insight", "understand"]):
            insight_fallbacks = ["Aurora Borealis", "Northern Lights", "Temple of Insight"]
            import random
            cleaned_title = random.choice(insight_fallbacks)
        elif any(term in user_answer_1.lower() + user_answer_2.lower() for term in ["space", "star", "planet", "galaxy", "universe"]):
            space_fallbacks = ["Andromeda", "Sirius", "Orion Nebula", "Milky Way"]
            import random
            cleaned_title = random.choice(space_fallbacks)
        else:
            fallbacks = ["Mount Olympus", "Great Barrier Reef", "Amazon Rainforest", "Stonehenge", "Himalayas"]
            import random
            cleaned_title = random.choice(fallbacks)
    
    print(f"🔍 Pre-capitalization place name: '{cleaned_title}'")
    
    short_title = ' '.join(word.capitalize() for word in cleaned_title.split())
    full_title = f"Guardian of {short_title}"
    
    print(f"🔍 Extracted place name: {short_title}")

    save_to_user_data("assignment", "title", short_title, index="title")
    save_to_user_data("assignment", "full_title", full_title, index="full_title")
    print(f"🌍 Assigned: {full_title}")
    return full_title

async def run_assignment_phase():
    user_data = load_user_data()
    user_name = user_data.get("user", {}).get("userName", "Querent")

    # 1. Maia introduces the assignment phase
    introduction_text = f"Revealing SOL does not come easily for humanity, but I believe you are worthy of this quest, {user_name}."
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
    await broadcast({
        "type": "full_inference",
        "user_question": user_response1,
        "llm_response": "Processing...", 
        "audio_url": None,
        "vision_image": "/static/captured.png" #maybe i'll use it
    })

    # 4. Maia responds to the first user response
    prompt1 = f"{system_prompt}\nRespond to the user's answer in a positive way. User: {user_response1}\n\nMAIA:"
    llm_output1 = run_llm(prompt1)
    clean_output1 = clean_llama_response(llm_output1) + " It is a grand place of existence."
    save_to_user_data("assignment", "maia_output_R1", clean_output1, index="R1")
    response1_audio = "maia_assignment_R1.wav"
    synthesize_speech(clean_output1, SPEAKER_WAV, os.path.join(STATIC_AUDIO_DIR, response1_audio))
    await broadcast({
        "type": "full_inference",
        "user_question": user_response1, 
        "llm_response": clean_output1,
        "audio_url": f"/static/audio/{response1_audio}",
        "vision_image": "/static/captured.png"
    })
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
    await broadcast({
        "type": "full_inference",
        "user_question": user_response2,
        "llm_response": "Processing...",
        "audio_url": None,
        "vision_image": "/static/captured.png"
    })

    # 7. Maia responds to the second user response
    prompt2 = f"{system_prompt}\nUser: {user_response2}\n\nMAIA:"
    llm_output2 = run_llm(prompt2)
    clean_output2 = clean_llama_response(llm_output2) + " And now a final question."
    save_to_user_data("assignment", "maia_output_R2", clean_output2, index="R2")
    response2_audio = "maia_assignment_R2.wav"
    synthesize_speech(clean_output2, SPEAKER_WAV, os.path.join(STATIC_AUDIO_DIR, response2_audio))
    await broadcast({
        "type": "full_inference",
        "user_question": user_response2,
        "llm_response": clean_output2,
        "audio_url": f"/static/audio/{response2_audio}",
        "vision_image": "/static/captured.png"
    })
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
    await broadcast({
        "type": "full_inference",
        "user_question": user_response3,
        "llm_response": "Processing...",
        "audio_url": None,
        "vision_image": "/static/captured.png"
    })

    # 10. Maia responds to the third user response
    prompt3 = f"{system_prompt}\nUser: {user_response3}\n\nMAIA:"
    llm_output3 = run_llm(prompt3)
    clean_output3 = clean_llama_response(llm_output3) + " This noble work is the light you need to continue to spread throughout. This comes from your SOL and makes you exceptional. Continue to spread that light!"
    save_to_user_data("assignment", "maia_output_R3", clean_output3, index="R3")
    response3_audio = "maia_assignment_R3.wav"
    synthesize_speech(clean_output3, SPEAKER_WAV, os.path.join(STATIC_AUDIO_DIR, response3_audio))
    await broadcast({
        "type": "full_inference",
        "user_question": user_response3,
        "llm_response": clean_output3,
        "audio_url": f"/static/audio/{response3_audio}",
        "vision_image": "/static/captured.png"
    })
    await play_audio_and_wait(response3_audio)

    final_title = generate_assignment()
    await broadcast({
        "type": "assignment_phase_complete",
        "assignment": final_title
    })
