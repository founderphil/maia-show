from pythonosc.udp_client import SimpleUDPClient
from backend.api.websocket_manager import WebSocketManager

ws_manager = WebSocketManager()

clients = set()

# OSC Client Setup
OSC_IP = "127.0.0.1"  
OSC_PORT = 7400  
osc_client = SimpleUDPClient(OSC_IP, OSC_PORT)

# Function to broadcast messages via WebSocket
async def broadcast(message: dict):
    """Broadcasts messages to all connected WebSocket clients."""
    import json
    for client in clients:
        try:
            await client.send_text(json.dumps(message))
        except Exception:
            clients.remove(client)