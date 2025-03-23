# MAIA Multi-sensory AI backend experience 

## Getting Started

install dependences, I suggest using conda too
run frontend:

```bash
npm run dev
```

run frontend:
```bash
python -m uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload
```
   - Local:        http://localhost:3000
   - Network:      http://192.168.1.165:3000 (get your IP on terminal with this): ipconfig getifaddr en0

http://127.0.0.1:8000
you can find the app on 192.168.1.XXX:3000. 
find your IP with ifconfig 

### arduino esp32
oscMAIA.ino runs on Arduino ESP32, connects to MAX

### TTS
IP voice sample excluded from repo!
for TTS you will need a voice sample to run inference. placed sample .wav file at /backend/models/stt_tts/models/ 

This is a [Next.js](https://nextjs.org) project bootstrapped with [`create-next-app`](https://nextjs.org/docs/app/api-reference/cli/create-next-app)