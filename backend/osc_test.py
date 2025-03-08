from pythonosc.osc_server import BlockingOSCUDPServer
from pythonosc.dispatcher import Dispatcher

def test_handler(address, *args):
    print(f"🔥 OSC Message Received: {address} {args}")

dispatcher = Dispatcher()
dispatcher.map("/ai_triggered", test_handler)  # Listening for "/ai_triggered"

server = BlockingOSCUDPServer(("127.0.0.1", 7500), dispatcher)
print("🎧 Listening for OSC messages on UDP port 8000...")
server.serve_forever()  # Keep listening