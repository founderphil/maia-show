from fastapi import APIRouter
from backend.api.pipelines.assignment_sequence import run_assignment_phase
from backend.utils.utils import osc_client

router = APIRouter()

@router.post("/start_assignment")
async def start_assignment_phase():
    print("🚀 Phase 4: Assignment started")
    osc_client.send_message("/phase/assignment", 1)

    assignment = await run_assignment_phase()

    return {"message": "Assignment phase complete", "assignment": assignment}
