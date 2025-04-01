import torch
import pickle
import os
from TTS.api import TTS
from backend.config import SPEAKER_WAV, STATIC_AUDIO_DIR

# Patch `torch.load` to fix potential Torch version mismatches
_original_torch_load = torch.load
def patched_torch_load(f, map_location=None, pickle_module=pickle, *, weights_only=True, mmap_mode=None, **pickle_load_args):
    if "mmap_mode" in pickle_load_args:
        del pickle_load_args["mmap_mode"]
    return _original_torch_load(f, map_location=map_location, pickle_module=pickle_module, weights_only=False, **pickle_load_args)

torch.load = patched_torch_load

# Import XTTS dependencies
from TTS.tts.configs.xtts_config import XttsConfig, XttsAudioConfig
from TTS.config.shared_configs import BaseDatasetConfig
from TTS.tts.models.xtts import XttsArgs

if hasattr(torch.serialization, "add_safe_globals"):
    torch.serialization.add_safe_globals([XttsConfig, XttsAudioConfig, BaseDatasetConfig, XttsArgs])

device = "cuda" if torch.cuda.is_available() else (
    "mps" if torch.backends.mps.is_available() and torch.backends.mps.is_built() else "cpu"
)

# Check if the operation may fail on MPS
if device == "mps":
    print("⚠️ MPS backend has known issues with spectrograms. Using CPU instead.")
    device = "cpu"
print(f"🔹 Using device: {device}")

tts = TTS("tts_models/multilingual/multi-dataset/xtts_v2")
tts.to(device)

def synthesize_speech(text: str, speaker_wav: str = SPEAKER_WAV, file_path: str = "maia_output.wav"): 
    if not text or not SPEAKER_WAV:
        raise ValueError("Both `text` and `SPEAKER_WAV` must be provided for synthesis.")

    input_text = text.strip()
    if not input_text:
        print("⚠️ No text provided for synthesis, skipping.")
        return

    tts.tts_to_file(
        text=input_text,
        speaker_wav=SPEAKER_WAV,
        language="en",
        file_path=file_path,
    )

    print(f"✅ Audio saved to {file_path}")


if __name__ == "__main__":
    sample_text = "Hello, this is MAIA speaking."
    output_path = os.path.join(STATIC_AUDIO_DIR, "maia_output.wav")  
    synthesize_speech(sample_text, output_path)