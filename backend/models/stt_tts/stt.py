# backend/stt_tts/stt.py
import os, requests, zipfile, io, wave, json
from vosk import Model, KaldiRecognizer
import sounddevice as sd
import numpy as np 
from backend.utils.utils import osc_client

SILENCE_THRESHOLD = 0.17  # Adjust based on environment noise level
SILENCE_DURATION = 3  # Stop recording after 1.5s of silence
SAMPLE_RATE = 16000  # Sample rate for Vosk STT

def download_and_extract_model(url: str, extract_to: str = "models"):
    os.makedirs(extract_to, exist_ok=True)
    print(f"Downloading model from {url}...")
    response = requests.get(url)
    if response.status_code == 200:
        print("Download complete. Extracting files...")
        with zipfile.ZipFile(io.BytesIO(response.content)) as z:
            z.extractall(path=extract_to)
        print("Extraction complete!")
    else:
        print("Failed to download model. Status code:", response.status_code)

BASE_DIR = os.path.dirname(__file__)
MODEL_PATH = os.path.join(BASE_DIR, "models", "vosk-model-small-en-us-0.15")

def transcribe_audio(audio_file_path: str) -> str:
    if not os.path.exists(MODEL_PATH):
        raise FileNotFoundError("Vosk model not found at " + MODEL_PATH)
    
    stt_model = Model(MODEL_PATH)
    wf = wave.open(audio_file_path, "rb")
    
    if wf.getnchannels() != 1 or wf.getsampwidth() != 2 or wf.getcomptype() != "NONE":
        raise ValueError("Audio file must be WAV format mono PCM.")
    
    rec = KaldiRecognizer(stt_model, wf.getframerate())
    result_text = ""
    
    while True:
        data = wf.readframes(4000)
        if len(data) == 0:
            break
        if rec.AcceptWaveform(data):
            res = json.loads(rec.Result())
            result_text += " " + res.get("text", "")
    
    res = json.loads(rec.FinalResult())
    result_text += " " + res.get("text", "")
    
    return result_text.strip()

def record_audio(output_filename="temp.wav", max_duration=None):
    """Records audio dynamically, stopping when silence is detected.
    If max_duration is None, only silence detection will stop recording.
    """
    print("🎙️ Listening... Speak now.")
    osc_client.send_message("/lighting/maiaLEDmode", 1)

    recording = []
    silence_start = None
    should_stop = [False]
    has_spoken = [False]

    def callback(indata, frames, time, status):
        nonlocal silence_start
        if should_stop[0]:
            return

        volume_norm = np.linalg.norm(indata) * 10
        recording.append(indata.copy())

        print(f"[DEBUG] volume_norm={volume_norm:.5f}, threshold={SILENCE_THRESHOLD}, silence_start={silence_start}, has_spoken={has_spoken[0]}")
        if not has_spoken[0]:
            if volume_norm >= SILENCE_THRESHOLD:
                has_spoken[0] = True
                print("[DEBUG] User has started speaking, enabling silence detection.")
            return

        # After user has spoken, enable silence detection
        if volume_norm < SILENCE_THRESHOLD:
            if silence_start is None:
                silence_start = time.inputBufferAdcTime
                print(f"[DEBUG] Silence started at {silence_start}")
            elif time.inputBufferAdcTime - silence_start > SILENCE_DURATION:
                print(f"[DEBUG] Silence detected for {SILENCE_DURATION} seconds, stopping recording.")
                should_stop[0] = True
                silence_start = None
        else:
            if silence_start is not None:
                print(f"[DEBUG] Sound detected, resetting silence timer.")
            silence_start = None

    try:
        with sd.InputStream(samplerate=SAMPLE_RATE, channels=1, callback=callback):
            if max_duration is not None:
                sd.sleep(max_duration * 1000)
            else:
                while not should_stop[0]:
                    sd.sleep(100)
    except sd.CallbackStop:
        pass

    print("[DEBUG] Exited recording loop, saving to file...")
    # Save to file
    recording = np.concatenate(recording, axis=0)
    print(f"[DEBUG] Concatenated recording shape: {recording.shape}")
    with wave.open(output_filename, "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(SAMPLE_RATE)
        wf.writeframes((recording * 32767).astype(np.int16).tobytes())
    print("[DEBUG] Audio written to file, sending OSC message...")
    osc_client.send_message("/lighting/maiaLEDmode", 2)
    print(f"✅ Recording saved: {output_filename}")
    return output_filename

if __name__ == "__main__":
    # Download model if not present
    if not os.path.exists(MODEL_PATH):
        model_url = "https://alphacephei.com/vosk/models/vosk-model-small-en-us-0.15.zip"
        download_and_extract_model(model_url, extract_to="models")
    
    record_audio("user_input.wav", record_seconds=5)
    transcription = transcribe_audio("user_input.wav")
    print("Transcription:", transcription)
