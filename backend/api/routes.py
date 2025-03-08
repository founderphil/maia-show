from fastapi import APIRouter
from backend.api.phases.tablet_phase import start_tablet_phase  # ✅ Import the function

router = APIRouter()

@router.post("/start_phase")  # ✅ Ensure this is registered
async def start_phase(data: dict):
    phase = data.get("phase")
    print(f"🔄 User changed phases to: {phase}")

    if phase == "tablet":
        return await start_tablet_phase()
    else:
        return {"message": f"Phase '{phase}' does not have a defined action"}