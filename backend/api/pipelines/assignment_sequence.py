import os, re, uuid, subprocess, asyncio
import soundfile as sf
from backend.models.stt_tts.stt import record_audio, transcribe_audio
from backend.models.stt_tts.tts import synthesize_speech
from backend.utils.utils import broadcast, save_to_user_data, load_user_data, osc_client
from backend.config import STATIC_AUDIO_DIR, SPEAKER_WAV, BASE_DIR, SYSTEM_PROMPT

os.makedirs(STATIC_AUDIO_DIR, exist_ok=True)
system_prompt = SYSTEM_PROMPT

def clean_llama_response(output_text: str) -> str:
    # Split by the delimiter that separates the model output
    parts = output_text.split("==========")
    if len(parts) > 1:
        answer_text = parts[1].strip()
    else:
        answer_text = output_text.strip()
    
    # Remove metadata lines
    answer_text = re.sub(r"Prompt:.*|Generation:.*|Peak memory:.*", "", answer_text, flags=re.DOTALL)
    
    # Check if we have any content after cleaning
    if not answer_text.strip():
        return "I sense your energy and connection to the universe. Your journey with SOL is just beginning."
    
    # Limit to first two sentences for brevity
    sentences = re.split(r'(?<=[.!?])\s+', answer_text)
    limited_output = ' '.join(sentences[:2])
    limited_output = re.sub(r"^(User:|MAIA:)\s*", "", limited_output)
    
    return limited_output.strip()

def run_llm(prompt: str, max_tokens: int = 128) -> str:
    model_path = os.path.join(BASE_DIR, "backend/models/llm/llama3_mlx")
    adapter_path = os.path.join(BASE_DIR, "backend/models/llm/adapters")
    result = subprocess.run([
    "mlx_lm.generate",
    "--model", model_path,
    "--adapter-path", adapter_path,
    "--prompt", prompt,
    "--max-tokens", str(max_tokens),
    "--temp", "0.0",  # Use --temp instead of --temperature
    "--top-p", "1.0"
    ], capture_output=True, text=True)
    print("🔍 LLM stdout:", result.stdout)
    print("🔍 LLM stderr:", result.stderr)  # Add stderr logging
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
    osc_client.send_message("/audio/play/voice/", {filename.strip()})
    await asyncio.sleep(get_duration_seconds(filepath) + 0.5)  # Add a small buffer to ensure playback is complete
    

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
    
    # Create a very direct prompt focused only on getting a place name
    summary_prompt = f"""You are MAIA, an AI tasked with assigning a fitting place to a user based on their responses to your questions.
You have asked the user three questions, and they have provided answers.
Based on this back and forth conversation between you, MAIA, and user answers, assign ONE celestial or terrestrial place to the user to protect.

Examples of assignment pairs:
User answer: "I love the stars and ancient cosmic mysteries."
Assignment: "Andromeda"
User answer: "I love the ocean and the sound of waves."
Assignment: "Pacific Ocean"
User answer: "I feel a connection to the ancient pyramids and their mysteries."
Assignment: "Great Pyramid of Giza"
User answer: "I love the mountains and the sound of the wind."
Assignment: "Mount Everest"
User answer: "I love the forest and the sound of birds."
Assignment: "Amazon Rainforest"
User answer: "I love the desert and the sound of silence."
Assignment: "Sahara Desert"
User answer: "I love the stars and ancient cosmic mysteries."
Assignment: "Milky Way"

Now the user’s conversation with you was:

MAIA question 1: "{maia_question_1}"
User answer 1: "{user_answer_1}"
MAIA question 2: "{maia_question_2}"
User answer 2: "{user_answer_2}"
MAIA question 3: "{maia_question_3}"
User answer 3: "{user_answer_3}"

Take this conversation, thinking about a place on earth that is inspired by the conversation, and create an Assignment.
Assignment should be a location on earth or space, without any additional text or explanation.
IMPORTANT: RESPOND WITH ONLY THE PHYSICAL NAME OF A PLACE OR LOCATION

Examples of Assignment: Mars, Andromeda, Pacific Ocean, Mount Everest, Neptune, Milky Way, Amazon Rainforest.
"""
    print("🔍 Summary Prompt for LLM:\n", summary_prompt)
    # Use a smaller max_tokens to force a shorter response
    raw_result = run_llm(summary_prompt, max_tokens=24)
    print("🔍 Raw LLM Output for Assignment:\n", raw_result)

    # Clean and extract just the place name
    cleaned_title = clean_llama_response(raw_result).strip()
    
    # Simple cleaning to get just the place name
    # Remove any quotes, periods, or other punctuation
    cleaned_title = cleaned_title.replace('"', '').replace("'", "").replace(".", "").strip()
    
    # Remove any common prefixes that aren't part of a place name
    prefixes_to_remove = ["the ", "a ", "an ", "guardian of ", "guardian ", "place: ", "place name: "]
    for prefix in prefixes_to_remove:
        if cleaned_title.lower().startswith(prefix):
            cleaned_title = cleaned_title[len(prefix):].strip()
    
    # If we still don't have a valid title or it contains problematic text, use a fallback
    if (not cleaned_title or 
        "[" in cleaned_title.lower() or 
        len(cleaned_title) > 30 or
        any(word in cleaned_title.lower() for word in ["guardian of", "creator", "light of", "sol", "querent"])):
        
        print("⚠️ Invalid place name generated, using fallback")
        
        # Analyze user responses to determine a relevant fallback
        if any(term in user_answer_1.lower() for term in ["ocean", "sea", "water", "beach", "wave"]):
            cleaned_title = "Pacific Ocean"
        elif any(term in user_answer_1.lower() + user_answer_2.lower() for term in ["space", "star", "planet", "galaxy", "universe"]):
            cleaned_title = "Andromeda"
        elif any(term in user_answer_2.lower() for term in ["book", "read", "knowledge", "wisdom", "ancient"]):
            cleaned_title = "Celestial Library"
        elif any(term in user_answer_3.lower() for term in ["light", "good", "see", "vision", "insight"]):
            cleaned_title = "Aurora Borealis"
        else:
            # Generic fallbacks based on the question themes
            fallbacks = ["Sirius", "Orion Nebula", "Mount Olympus", "Great Barrier Reef", "Amazon Rainforest"]
            import random
            cleaned_title = random.choice(fallbacks)
    
    print(f"🔍 Pre-capitalization place name: '{cleaned_title}'")
    
    # Capitalize the first letter of each word
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
        "llm_response": "Processing...", # Placeholder until LLM runs
        "audio_url": None,
        "vision_image": "/static/captured.png" # Assuming vision isn't updated here
    })

    # 4. Maia responds to the first user response
    prompt1 = f"{system_prompt}\nUser: {user_response1}\n\nMAIA:"
    llm_output1 = run_llm(prompt1)
    clean_output1 = clean_llama_response(llm_output1) + " It is a grand place of existence."
    save_to_user_data("assignment", "maia_output_R1", clean_output1, index="R1")
    response1_audio = "maia_assignment_R1.wav"
    synthesize_speech(clean_output1, SPEAKER_WAV, os.path.join(STATIC_AUDIO_DIR, response1_audio))
    await broadcast({
        "type": "full_inference",
        "user_question": user_response1, # From previous step
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
