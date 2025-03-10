import torch
import pickle
import os
from TTS.api import TTS


_original_torch_load = torch.load

def patched_torch_load(f, map_location=None, pickle_module=pickle, *, weights_only=True, mmap_mode=None, **pickle_load_args):
    if "mmap_mode" in pickle_load_args:
        del pickle_load_args["mmap_mode"]
    return _original_torch_load(f, map_location=map_location, pickle_module=pickle_module, weights_only=False, **pickle_load_args)

torch.load = patched_torch_load

from TTS.tts.configs.xtts_config import XttsConfig, XttsAudioConfig
from TTS.config.shared_configs import BaseDatasetConfig
from TTS.tts.models.xtts import XttsArgs

# Only add safe globals if available (Torch 2.3+); Torch 2.2.2 doesn't have it.
if hasattr(torch.serialization, "add_safe_globals"):
    torch.serialization.add_safe_globals([XttsConfig, XttsAudioConfig, BaseDatasetConfig, XttsArgs])

BASE_DIR = os.path.dirname(os.path.abspath(__file__)) 
SPEAKER_WAV_PATH = os.path.join(BASE_DIR, "patricia_full.wav")

def synthesize_speech(text: str, speaker_wav: str = SPEAKER_WAV_PATH, file_path: str = "maia_output.wav"): 
    """Runs speech synthesis with voice cloning (Coqui XTTSv2)."""
    if not text or not speaker_wav:
        raise ValueError("Both `text` and `speaker_wav` must be provided for synthesis.")

    device = "cuda" if torch.cuda.is_available() else "cpu"
    tts = TTS("tts_models/multilingual/multi-dataset/xtts_v2", progress_bar=False, gpu=torch.cuda.is_available())
    tts.to(device)

    tts.tts_to_file(
        text=text,
        speaker_wav=speaker_wav, 
        language="en",
        file_path=file_path
    )
    print(f"✅ Audio saved to {file_path}")


if __name__ == "__main__":
    sample_text = "Hello, this is MAIA speaking."
    file_path = os.path.join(BASE_DIR, "maia_output.wav")  
    synthesize_speech(sample_text, SPEAKER_WAV_PATH, file_path)