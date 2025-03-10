from fastapi import FastAPI, WebSocket
import json
from contextlib import asynccontextmanager
from pythonosc.dispatcher import Dispatcher
from pythonosc.osc_server import AsyncIOOSCUDPServer
from pythonosc.udp_client import SimpleUDPClient
import asyncio
from backend.api.routes import router as api_router
from backend.api.phases import tablet_phase
from fastapi.middleware.cors import CORSMiddleware
from backend.api.postshow import router as postshow_router

app = FastAPI()

app.include_router(api_router, prefix="/api")
app.include_router(tablet_phase.router, prefix="/api")
app.include_router(postshow_router, prefix="/api")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# OSC Client Setup
OSC_IP = "127.0.0.1"  
OSC_PORT = 7400  
osc_client = SimpleUDPClient(OSC_IP, OSC_PORT)
clients = []
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
    await websocket.accept()
    clients.append(websocket)

    try:
        while True:
            data = await websocket.receive_text()
            message = json.loads(data)
            # handler for lights
            if message["type"] == "lighting_update":
                print(f"Lighting update: {message['light']} -> {message['value']}")
                osc_client.send_message(f"/lighting/{message['light']}", message["value"])
                await broadcast({"type": "lighting_status", "light": message["light"], "value": message["value"]})
            # handler for AI Pipelines
            elif message["type"] == "ai_command":
                print(f"AI Pipeline Command: {message['pipeline']} -> {message['command']}")
                osc_client.send_message(f"/ai/{message['pipeline']}", message["command"])
                await broadcast({"type": "ai_status", "pipeline": message["pipeline"], "status": message["command"]})
            # handler for user data
            elif message["type"] == "user_data":
                print(f"User Data: {message['data']}")
                await broadcast({"type": "user_data_received", "data": message["data"]})
            # handler for phase change
            elif message["type"] == "phase_change":
                print(f"User changed phase to: {message['phase']}")
                osc_client.send_message("/phase", message["phase"])
                await broadcast({"type": "phase_updated", "phase": message["phase"]})

    except Exception as e:
        print("WebSocket error:", e)
    finally:
        clients.remove(websocket)

# Broadcast function
async def broadcast(message: dict):
    for client in clients:
        try:
            await client.send_text(json.dumps(message))
        except Exception:
            clients.remove(client)