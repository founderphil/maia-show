import json
from fastapi import WebSocket

class WebSocketManager:
    def __init__(self):
        self.clients = set()

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.clients.add(websocket)

    async def disconnect(self, websocket: WebSocket):
        if websocket in self.clients:
            self.clients.discard(websocket)

    async def broadcast(self, message: dict):
        """Send a message to all WebSocket clients."""
        to_remove = set()
        for client in self.clients:
            try:
                await client.send_text(json.dumps(message))
            except Exception:
                to_remove.add(client)

        for client in to_remove:
            self.clients.discard(client)

# ✅ Global instance
ws_manager = WebSocketManager()