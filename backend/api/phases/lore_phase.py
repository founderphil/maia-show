from fastapi import APIRouter
import asyncio, os, json
from asyncio import Event, create_task
from backend.api.pipelines.tts_only import run_tts_only
from backend.api.pipelines.question_llm_tts import run_question_sequence
from backend.utils.utils import save_to_user_data, broadcast, get_wav_duration, osc_client
from backend.config import BASE_DIR, USER_DATA_FILE, STATIC_AUDIO_DIR
from backend.api.phases.assignment_phase import start_assignment_phase

router = APIRouter()
audio_done_event = Event()

def load_user_data():
    """Load the latest user data from `user_data.json`."""
    user_data_path = os.path.join(BASE_DIR, USER_DATA_FILE)
    if os.path.exists(user_data_path):
        with open(user_data_path, "r") as f:
            return json.load(f).get("user", {})
    return {}

# Function to pre-generate TTS files for assignment phase
async def pregenerate_assignment_audio(user_name):
    # Pre-generate assignment intro
    intro_text = f"Revealing SOL does not come easily for humanity, but I believe you are worthy of this quest, {user_name}."
    await run_tts_only(tts_text=intro_text, filename="maia_assignment_intro.wav")
    
    # Pre-generate assignment questions
    q1_text = "You are standing in a place where the universe breathes around you. Describe to me your favorite place in the universe."
    await run_tts_only(tts_text=q1_text, filename="maia_assignment_Q1.wav")
    
    q2_text = "You come across something ancient. What is it and what do you do?"
    await run_tts_only(tts_text=q2_text, filename="maia_assignment_Q2.wav")
    
    # Pre-generate Q3 as well
    q3_text = ("Tell me, when the universe listens to the quiet murmur of your soul. "
              "What hidden spark within you does it reveal? What do you believe is your gift or talent?")
    await run_tts_only(tts_text=q3_text, filename="maia_assignment_Q3.wav")

# Function to pre-generate farewell audio for departure phase
async def pregenerate_farewell_audio(user_name):
    farewell_text = (
        f"I see the light of SOL within you {user_name}. "
        f"Your talents shine through you like a neutron star. "
        f"It is with great honor, on behalf of all the Enlightened Ones, to knight you a guardian of SOL. "
        f"Go forth, Guardian. And remember that the light will always outshine the darkness."
    )
    await run_tts_only(tts_text=farewell_text, filename="maia_departure.wav")

@router.post("/start_lore")
async def start_lore_phase():
    print("🚀 Starting Phase 3: Lore")

    # Cue lights/audio in MAX MSP
    osc_client.send_message("/phase/lore", 1)

    print("Play Lore Movie!")
    osc_client.send_message("/video/play/", "Maia_Lore_cut.mp4")
    patricia_path = os.path.join(STATIC_AUDIO_DIR, "Lore_Audio.wav")
    lore_duration = get_wav_duration(patricia_path)
    print("🔊 Playing THE LORE STORY VIDEO in MAX MSP, next generate inference...")

    user_data = load_user_data()
    user_name = user_data.get("userName", "Querent")

    # Scripted welcome TTS
    scripted_text = (
        f"And now that battle to protect the last remnants of SOL comes to you. "
        f"I come to you {user_name} and ask you to protect the light. "
        f"A guardianship, passed on from The Enlightened Ones. "
        f"Before you take up this higher calling. What questions do you have for me, {user_name}?"
    )

    # Start TTS generation for lore Q intro
    lore_tts_task = create_task(run_tts_only(tts_text=scripted_text, filename="maia_lore_Q_intro.wav"))
    
    # Start background tasks to pre-generate audio for later phases
    # These will run concurrently during the lore video playback
    assignment_audio_task = create_task(pregenerate_assignment_audio(user_name))
    farewell_audio_task = create_task(pregenerate_farewell_audio(user_name))
    
    # Wait for lore TTS to complete and save result
    tts_result = await lore_tts_task
    save_to_user_data("lore", "maia", tts_result["llm_response"])
    
    # Calculate the appropriate wait time based on the actual duration of the lore video
    # and the processing times we've already accounted for
    lore_audio_path = os.path.join(STATIC_AUDIO_DIR, "Lore_Audio.wav")
    if os.path.exists(lore_audio_path):
        lore_duration = get_wav_duration(lore_audio_path)
        print(f"🔍 Lore video duration: {lore_duration} seconds")
        
        # Subtract a small buffer to ensure we don't cut off the video
        wait_time = max(lore_duration - 4, 60)  # Minimum 60 seconds wait
        print(f"⏳ Waiting {wait_time} seconds for lore video to finish...")
        await asyncio.sleep(wait_time)
    else:
        print("⚠️ Lore_Audio.wav not found, using default wait time")
        await asyncio.sleep(66)  # Default wait time
    
    # By this point, the background TTS tasks should be complete or nearly complete
    osc_client.send_message("/audio/play/voice/", "maia_lore_Q_intro.wav")  ###### PLAY LORE ENDING audio
    
    # Get the duration of the lore Q intro audio
    lore_q_intro_path = os.path.join(STATIC_AUDIO_DIR, "maia_lore_Q_intro.wav")
    if os.path.exists(lore_q_intro_path):
        lore_q_intro_duration = get_wav_duration(lore_q_intro_path)
        print(f"🔍 Lore Q intro duration: {lore_q_intro_duration} seconds")
        # Add a small buffer to ensure the audio completes
        wait_time = lore_q_intro_duration + 2
        print(f"⏳ Waiting {wait_time} seconds for lore Q intro to finish...")
        await asyncio.sleep(wait_time)
    else:
        print("⚠️ maia_lore_Q_intro.wav not found, using default wait time")
        await asyncio.sleep(22)  # Default wait time
    
    # Make sure all background TTS tasks are complete
    if not assignment_audio_task.done():
        await assignment_audio_task
    if not farewell_audio_task.done():
        await farewell_audio_task

    await broadcast({
        "type": "phase_lore",
        "phase": "lore",
        "message": "Phase 3 - Lore Started",
        "llm_response": scripted_text,
        "audio_url": "/static/audio/maia_lore_Q_intro.wav"
    })

    # Interactive Q&A sequence
    print("✨ Entering Lore Q&A Phase")
    await run_question_sequence()

    await start_assignment_phase() # Start the assignment phase after Q&A is complete
    await asyncio.sleep(2)  
    return {"message": "Phase 3 - Lore Phase with Q&A Completed"}
