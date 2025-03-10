# backend/stt_tts/stt.py
import os
import requests
import zipfile
import io
import wave
import json
from vosk import Model, KaldiRecognizer
import pyaudio

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

def record_audio(filename: str, record_seconds: int = 5, sample_rate: int = 16000, channels: int = 1, chunk: int = 1024):
    audio = pyaudio.PyAudio()
    stream = audio.open(format=pyaudio.paInt16,
                        channels=channels,
                        rate=sample_rate,
                        input=True,
                        frames_per_buffer=chunk)
    
    print("Recording audio...")
    frames = []
    for _ in range(0, int(sample_rate / chunk * record_seconds)):
        data = stream.read(chunk)
        frames.append(data)
    
    stream.stop_stream()
    stream.close()
    audio.terminate()
    
    with wave.open(filename, 'wb') as wf:
        wf.setnchannels(channels)
        wf.setsampwidth(audio.get_sample_size(pyaudio.paInt16))
        wf.setframerate(sample_rate)
        wf.writeframes(b''.join(frames))
    print("Audio recorded and saved to", filename)

if __name__ == "__main__":
    # Download model if not present
    if not os.path.exists(MODEL_PATH):
        model_url = "https://alphacephei.com/vosk/models/vosk-model-small-en-us-0.15.zip"
        download_and_extract_model(model_url, extract_to="models")
    
    record_audio("user_input.wav", record_seconds=5)
    transcription = transcribe_audio("user_input.wav")
    print("Transcription:", transcription)