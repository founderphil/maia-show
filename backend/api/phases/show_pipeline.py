import asyncio
from backend.api.phases.tablet_phase import start_tablet_phase
from backend.api.phases.intro_phase import start_intro_phase
from backend.api.phases.lore_phase import start_lore_phase
from backend.api.phases.assign_phase import start_assign_phase
from backend.api.phases.depart_phase import start_depart_phase

async def start_full_show():
    """Runs all phases sequentially."""
    print("🎬 Starting Full Show Run")

    await start_tablet_phase()
    await asyncio.sleep(2)  # Delay between phases

    await start_intro_phase()
    await asyncio.sleep(2)  

    await start_lore_phase()
    await asyncio.sleep(2)  

    await start_assign_phase()
    await asyncio.sleep(2)  

    await start_depart_phase()
    print("🏁 Show Completed")