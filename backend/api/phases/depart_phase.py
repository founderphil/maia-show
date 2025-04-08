import os, asyncio, subprocess
from fastapi import APIRouter
from backend.api.pipelines.tts_only import run_tts_only
from backend.utils.utils import load_user_data
from backend.config import STATIC_AUDIO_DIR
from pythonosc.udp_client import SimpleUDPClient

from pyfiglet import Figlet, FigletFont
from PIL import Image, ImageDraw, ImageFont

router = APIRouter()
client = SimpleUDPClient("127.0.0.1", 7400)

def generate_combined_certificate(user_name, final_title, ascii_img_path, certificate_text_path, output_path="static/images/printable_certificate.png"):

    ascii_img = Image.open(ascii_img_path).convert("RGB")
    ascii_width, ascii_height = ascii_img.size
    portrait_width = int(8.5 * 300)
    portrait_height = int(11 * 300)
    combined = Image.new("RGB", (portrait_width, portrait_height), "white")
    draw = ImageDraw.Draw(combined)
    ascii_scale = portrait_width * 0.9 #/ ascii_width
    resized_ascii = ascii_img.resize(
        (int(ascii_width * ascii_scale), int(ascii_height * ascii_scale))
    )
    ascii_x = (portrait_width - resized_ascii.width) // 2
    combined.paste(resized_ascii, (ascii_x, 100))

    # Load font
    try:
        font = ImageFont.truetype("Courier_New.ttf", 48)
    except:
        font = ImageFont.load_default()
    with open(certificate_text_path, "r") as f:
        lines = f.readlines()

    #margins
    y_start = resized_ascii.height + 300
    x_margin = 300
    y = y_start

    for line in lines:
        draw.text((x_margin, y), line.strip(), fill="black", font=font)
        y += 70

    combined.save(output_path)
    print(f"🖼️ Portrait certificate saved: {output_path}")
    subprocess.run(["lp", output_path])

@router.post("/start_departure")
async def start_departure_phase():
    print("🌌 Phase 5: Departure")

    user_data = load_user_data()
    user_name = user_data.get("user", {}).get("userName", "Querent")
    final_title = user_data.get("assignment", {}).get("full_title", "Guardian of Unknown")
    ascii_title = user_data.get("assignment", {}).get("title", "Unknown Realm")

    farewell_text = (
        f"I see the light of SOL within you {user_name}. "
        f"Your talents shine through you like a neutron star. "
        f"It is with great honor, on behalf of all the Enlightened Ones, to knight you a guardian of SOL. "
        f"Go forth, Guardian. And remember that the light will always outshine the darkness."
    )

    # Speak farewell message
    await run_tts_only(tts_text=farewell_text, filename="maia_departure.wav")
    client.send_message("/audio/play/voice/", "maia_departure.wav")
    await asyncio.sleep(10)

    # Lights cue
    lighting_off = {
        "maiaLED": 0,
        "houseLight1": 100,
        "houseLight2": 100,
        "chairSpot": 0,
        "maiaSpot1": 0,
        "maiaSpot2": 0,
        "maiaProjector1": 0,
        "maiaProjector2": 0,
    }
    for light, value in lighting_off.items():
        client.send_message(f"/lighting/{light}", value)

    certificate_text = f"""
{user_name}.
THE ENLIGHTENED ONES HAVE DEEMED YOU A GUARDIAN OF SOL.
IT IS NOW YOUR DUTY TO PROTECT THE LIGHT OF CREATION.

YOU ARE THE {final_title.upper()}

I AM HERE FOR YOU.
MAIA
—------------------------
Leave your message for a fellow guardian.
—------------------------
    """.strip()

    print_path = os.path.join(STATIC_AUDIO_DIR, "certificate.txt")
    with open(print_path, "w") as f:
        f.write(certificate_text)

    # Create and print combined image
    generate_combined_certificate(user_name, final_title, "static/images/ascii_title.png", print_path)

    return {"message": "Phase 5 - Departure completed."}