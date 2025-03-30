from fastapi import APIRouter
from pythonosc.udp_client import SimpleUDPClient
from backend.api.pipelines.assignment_sequence import run_assignment_sequence

router = APIRouter()
OSC_IP = "127.0.0.1"
OSC_PORT = 7400
client = SimpleUDPClient(OSC_IP, OSC_PORT)

@router.post("/start_assignment")
async def start_assignment_phase():
    print("🚀 Phase 4: Assignment started")
    client.send_message("/phase/assignment", 1)

    assignment = await run_assignment_sequence()
    print(f"🌍 Assigned: Guardian of {assignment}")

    return {"message": "Assignment phase complete", "assignment": assignment}