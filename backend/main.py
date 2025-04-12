from backend.utils.utils import osc_client
from backend.api.websocket_manager import ws_manager
from fastapi import FastAPI, WebSocket
import json
import asyncio
from contextlib import asynccontextmanager
from pythonosc.dispatcher import Dispatcher
from pythonosc.osc_server import AsyncIOOSCUDPServer
from backend.api.routes import router as api_router
from backend.api.phases import tablet_phase
from fastapi.middleware.cors import CORSMiddleware
from backend.api.postshow import router as postshow_router
from backend.api.phases.show_pipeline import start_full_show 
from backend.api.phases.intro_phase import router as intro_phase_router
from fastapi.staticfiles import StaticFiles
app = FastAPI()

app.include_router(api_router, prefix="/api")
app.include_router(tablet_phase.router, prefix="/api")
app.include_router(postshow_router, prefix="/api")
app.include_router(intro_phase_router, prefix="/api")
app.mount("/static", StaticFiles(directory="static"), name="static")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

pause_event = asyncio.Event()

# OSC Message Handler
def osc_handler(address, *args):
    print(f"🚀 Received OSC from MAX MSP: {address} {args}")

dispatcher = Dispatcher()
dispatcher.map("/ai_triggered", osc_handler)

# Start OSC Server
async def start_osc_server():
    server = AsyncIOOSCUDPServer(("127.0.0.1", 8000), dispatcher, asyncio.get_running_loop())
    transport, protocol = await server.create_serve_endpoint()
    return transport, protocol

@asynccontextmanager
async def lifespan(app: FastAPI):
    transport, protocol = await start_osc_server()
    yield
    transport.close()

# WebSocket Endpoint
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """Handles WebSocket connections and forwards messages."""
    await ws_manager.connect(websocket)  
    try:
        while True:
            data = await websocket.receive_text()
            message = json.loads(data)

            # 🎬 Showrunner Controls (Play, Pause, Reset)
            global pause_event
            if message["type"] == "show_control":
                command = message["command"]
                print(f"🎬 Show Control Command: {command}")

                if command == "play":
                    if pause_event.is_set():
                        print("▶️ Resuming show.")
                        pause_event.clear()
                    await start_full_show() 
                elif command == "pause":
                    print("⏸️ Pausing show, setting house lights to full.")
                    osc_client.send_message("/lighting/houseLight", 1)
                    osc_client.send_message("/lighting/houseLight", 1)
                    print("⏳ Waiting for 'play' to resume...")
                    await pause_event.wait() 
                    print("▶️ Resumed after pause.")
                elif command == "reset":
                    print("🔄 Resetting show.")
                    await tablet_phase.reset_room()

            # Lighting Controls
            elif message["type"] == "lighting_update":
                print(f"Lighting update: {message['light']} -> {message['value']}")
                osc_client.send_message(f"/lighting/{message['light']}", message["value"])
                await ws_manager.broadcast({"type": "lighting_status", "light": message["light"], "value": message["value"]})

            # AI Pipeline Controls
            elif message["type"] == "ai_command":
                print(f"AI Pipeline Command: {message['pipeline']} -> {message['command']}")
                osc_client.send_message(f"/ai/{message['pipeline']}", message["command"])
                await ws_manager.broadcast({"type": "ai_status", "pipeline": message["pipeline"], "status": message["command"]})

            # User Data Updates
            elif message["type"] == "user_data":
                print(f"User Data: {message['data']}")
                await ws_manager.broadcast({"type": "user_data_received", "data": message["data"]})

            # Phase Changes
            elif message["type"] == "phase_change":
                print(f"User changed phase to: {message['phase']}")
                osc_client.send_message("/phase", message["phase"])
                await ws_manager.broadcast({"type": "phase_updated", "phase": message["phase"]})

    except Exception as e:
        print("WebSocket error:", e)
    finally:
        await ws_manager.disconnect(websocket)   

# The broadcast function has been moved to utils.py and now uses ws_manager
