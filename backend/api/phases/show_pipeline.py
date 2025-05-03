import asyncio
from backend.api.pipelines.greetings_tts import tts_greeting
from backend.api.pipelines.tts_only import run_tts_only
from backend.api.phases.intro_phase import start_intro_phase
from backend.api.phases.lore_phase import start_lore_phase
from backend.api.phases.assignment_phase import start_assignment_phase
from backend.api.phases.depart_phase import start_departure_phase

async def start_full_show():
    """Runs all phases sequentially."""
    print("🎬 Starting Full Show Run")

    # Run TTS jobs sequentially: greeting first, then welcome
    await tts_greeting(filename="maia_greeting.wav")
    await run_tts_only(filename="maia_output_welcome.wav")
    await asyncio.sleep(2)  # Delay between phases

    await start_intro_phase()
    await asyncio.sleep(2)  

    await start_lore_phase()
    await asyncio.sleep(2)  

    await start_assignment_phase()
    await asyncio.sleep(2)  

    await start_departure_phase()
    print("🏁 Show Completed")
