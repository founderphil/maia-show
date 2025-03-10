from fastapi import APIRouter
import json
import os

router = APIRouter()
USER_DATA_FILE = "user_data.json"

def load_user_data():
    if os.path.exists(USER_DATA_FILE):
        with open(USER_DATA_FILE, "r") as f:
            return json.load(f)
    return {}

@router.post("/postshow/saveAll")
async def save_all():
    """Save the full profile to cloud."""
    if not os.path.exists(USER_DATA_FILE):
        return {"error": "No user data found"}

    with open(USER_DATA_FILE, "r") as f:
        user_data = json.load(f)

    # TODO: Simulated cloud upload!!!
    return {"message": "Full profile sent to FAIRYLAND", "data": user_data}

@router.post("/postshow/saveSelected")
async def save_selected(selected_data: dict):
    """Save only selected fields to cloud."""
    if not selected_data:
        return {"error": "No data selected"}
    
    # TODO: Simulated cloud upload!!!
    return {"message": "Selected data sent to FAIRYLAND", "data": selected_data}

@router.delete("/postshow/deleteAll")
async def delete_all():
    """Delete all local user data."""
    if os.path.exists(USER_DATA_FILE):
        os.remove(USER_DATA_FILE)
        return {"message": "All session data has been deleted"}
    return {"error": "No data to delete"}