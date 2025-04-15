from fastapi import APIRouter
import json
import os
import glob
from backend.config import USER_DATA_FILE, STATIC_AUDIO_DIR

router = APIRouter()

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

    return {"message": "Full profile sent to FAIRYLAND", "data": user_data}

@router.post("/postshow/saveSelected")
async def save_selected(selected_data: dict):
    """Save only selected fields to cloud."""
    if not selected_data:
        return {"error": "No data selected"}
    
    return {"message": "Selected data sent to FAIRYLAND", "data": selected_data}

@router.delete("/postshow/deleteAll")
async def delete_all():
    """Delete all local user data and generated audio files."""
    deleted_data = False
    deleted_audio = False
    
    # Delete user data file
    if os.path.exists(USER_DATA_FILE):
        os.remove(USER_DATA_FILE)
        deleted_data = True
    
    # Delete generated audio files
    audio_patterns = [
        os.path.join(STATIC_AUDIO_DIR, "maia_output_*.wav"),
        os.path.join(STATIC_AUDIO_DIR, "maia_assignment_R*.wav"),
        os.path.join(STATIC_AUDIO_DIR, "maia_assignment_intro.wav"),
        os.path.join(STATIC_AUDIO_DIR, "maia_departure.wav"),
        os.path.join(STATIC_AUDIO_DIR, "maia_greeting.wav"),
        os.path.join(STATIC_AUDIO_DIR, "maia_lore_*.wav")
    ]
    
    deleted_files_count = 0
    for pattern in audio_patterns:
        audio_files = glob.glob(pattern)
        for audio_file in audio_files:
            try:
                os.remove(audio_file)
                deleted_files_count += 1
                deleted_audio = True
            except Exception as e:
                print(f"Error deleting audio file {audio_file}: {e}")
    
    if deleted_audio:
        print(f"Deleted {deleted_files_count} audio files")
    
    if deleted_data and deleted_audio:
        return {"message": "All session data and generated audio files have been deleted"}
    elif deleted_data:
        return {"message": "All session data has been deleted, but no audio files were found"}
    elif deleted_audio:
        return {"message": "Generated audio files have been deleted, but no user data was found"}
    else:
        return {"error": "No data or audio files to delete"}
