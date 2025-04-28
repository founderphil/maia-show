import os, asyncio, subprocess
from fastapi import APIRouter
from backend.api.pipelines.tts_only import run_tts_only
from backend.utils.utils import load_user_data, osc_client
from backend.config import STATIC_AUDIO_DIR

from PIL import Image, ImageDraw, ImageFont
import textwrap

router = APIRouter()

def print_certificate_text(certificate_text, user_name=None, output_path="static/images/printable_certificate.png"):

    if user_name is None:

        first_line = certificate_text.split('\n')[0].strip()
        if "..." in first_line:
            user_name = first_line.split('...')[0].strip()
        else:
            user_name = "User"
    #page size        
    portrait_width = int(8.5 * 300)
    portrait_height = int(11 * 300)
    combined = Image.new("RGB", (portrait_width, portrait_height), "white")
    draw = ImageDraw.Draw(combined)
    

    margin_left = int(0.75 * 300) 
    margin_right = int(0.75 * 300)
    usable_width = portrait_width - margin_left - margin_right
    
    try:
        monospace_fonts = [
            "/System/Library/Fonts/Courier.dfont",
            "/System/Library/Fonts/Monaco.dfont",
            "/System/Library/Fonts/Menlo.ttc",
            "/System/Library/Fonts/Courier New.ttf",
            "/System/Library/Fonts/Andale Mono.ttf"
        ]
        regular_fonts = [
            "/System/Library/Fonts/Supplemental/Zapfino.ttf",  
            "/System/Library/Fonts/Supplemental/Didot.ttc",
            "/System/Library/Fonts/Supplemental/Times New Roman.ttf",
            "/Library/Fonts/Arial.ttf",
            "/System/Library/Fonts/Helvetica.ttc"
        ]
        
        ascii_font_loaded = False
        for font_path in monospace_fonts:
            if os.path.exists(font_path):
                try:
                    ascii_font = ImageFont.truetype(font_path, 30)
                    ascii_font_loaded = True
                    print(f"ASCII font loaded successfully from {font_path}")
                    break
                except Exception as e:
                    print(f"Error loading ASCII font {font_path}: {e}")
                    continue
        
        # Load regular fonts for text
        regular_font_loaded = False
        for font_path in regular_fonts:
            if os.path.exists(font_path):
                try:
                    title_font = ImageFont.truetype(font_path, 58)
                    subtitle_font = ImageFont.truetype(font_path, 50)
                    body_font = ImageFont.truetype(font_path, 42)
                    regular_font_loaded = True
                    print(f"Regular fonts loaded successfully from {font_path}")
                    break
                except Exception as e:
                    print(f"Error loading regular font {font_path}: {e}")
                    continue
        
        # Fall back to default fonts
        if not ascii_font_loaded:
            print("Using default font for ASCII art")
            ascii_font = ImageFont.load_default()
            
        if not regular_font_loaded:
            print("Using default fonts for regular text")
            title_font = ImageFont.load_default()
            subtitle_font = ImageFont.load_default()
            body_font = ImageFont.load_default()
            
    except Exception as e:
        print(f"Error loading fonts: {e}")
        title_font = ImageFont.load_default()
        subtitle_font = ImageFont.load_default()
        body_font = ImageFont.load_default()
        ascii_font = ImageFont.load_default()
    
    lines = certificate_text.split('\n')
    y = 100
    in_ascii_art = False
    
    for line in lines:
        # Check if ASCII art
        if "@@@@" in line or "@@@" in line or "@@" in line or "@" in line or ":" in line or "#" in line:
            in_ascii_art = True
            font = ascii_font
            line_spacing = 30 
            
            if line.strip(): 
                try:
                    text_width = draw.textlength(line, font=font)
                except:
                    text_width, _ = draw.textsize(line, font=font)
                x = (portrait_width - text_width) // 2
                draw.text((x, y), line, fill="black", font=font)
                y += line_spacing
            else:
                y += 5 
                
        elif line.strip() == "" and in_ascii_art:
            in_ascii_art = False
            y += 20  # Add space after ASCII art
            continue
            
        elif not in_ascii_art:
            if not line.strip():
                y += 40
                continue
                
            if user_name in line and "..." in line:
                font = title_font
                line_spacing = 150
            elif "The Enlightened Ones" in line or "Guardian of Sol" in line:
                font = title_font
                line_spacing = 100
            elif "You are the" in line:
                font = subtitle_font
                line_spacing = 200
            elif "Maia" in line:
                font = title_font
                line_spacing = 150
            elif "—-" in line:
                font = body_font
                line_spacing = 60
            else:
                font = body_font
                line_spacing = 100
            
            trimmed_line = line.strip()
            
            try:
                text_width = draw.textlength(trimmed_line, font=font)
            except:
                text_width, _ = draw.textsize(trimmed_line, font=font)
            
            if text_width > usable_width:
                avg_char_width = text_width / len(trimmed_line)
                chars_per_line = int(usable_width / avg_char_width)
                wrapped_lines = textwrap.wrap(trimmed_line, width=chars_per_line)
                
                for wrapped_line in wrapped_lines:
                    try:
                        wrapped_width = draw.textlength(wrapped_line, font=font)
                    except:
                        wrapped_width, _ = draw.textsize(wrapped_line, font=font)
                
                    x = (portrait_width - wrapped_width) // 2
                    draw.text((x, y), wrapped_line, fill="black", font=font)
                    y += line_spacing
            else:
                x = (portrait_width - text_width) // 2
                draw.text((x, y), trimmed_line, fill="black", font=font)
                y += line_spacing
    
    # Save the certificate as a PNG file
    combined.save(output_path)
    print(f"🖼️ Certificate saved: {output_path}")
    
    # Print the certificate
    try:
            subprocess.run(["lp", output_path])
            print("🖨️ Certificate sent to printer")
    except Exception as e:
            print(f"Error printing certificate: {e}")

@router.post("/start_departure")
async def start_departure_phase():
    print("🌌 Phase 5: Departure")

    user_data = load_user_data()
    user_name = user_data.get("user", {}).get("userName", "Querent")
    
    final_title = None
    if final_title is None:
        final_title = user_data.get("assignment", {}).get("full_title")
    
    if final_title is None:
        final_title = user_data.get("user", {}).get("assignment.maia_output_full_title")
    
    if final_title is None:
        final_title = "Guardian of Unknown"

    farewell_text = (
        f"I see the light of SOL within you {user_name}. "
        f"Your talents shine through you like a neutron star. "
        f"It is with great honor, on behalf of all the Enlightened Ones, to knight you a guardian of SOL. "
        f"Go forth, Guardian. And remember that the light will always outshine the darkness."
    )
##### speak farewell
    if not os.path.exists(os.path.join(STATIC_AUDIO_DIR, "maia_departure.wav")):
        await run_tts_only(tts_text=farewell_text, filename="maia_departure.wav")
    osc_client.send_message("/audio/play/voice/", "maia_departure.wav")
    osc_client.send_message("/audio/play/music/", "full.mp3")

    certificate_text = f""" 
                                          {user_name}...                                                          
                                                                                                    
                                       :@@@@@@#=-::=*%@@@@@*                                        
                                  #@@:                       @@@*                                   
                              +@+                                %@%                                
                           +@:             :*@@@@@@@@@@=.           @@=        .                    
                         @=          +@@@@@@@@#+-.:=*%@@@@@@@.        #@%        .                  
                       @         +@@@@#                    +@@@@#       @@:       -                 
                     @        -@@@#              ::           .@@@@       @@       =                
                   #+       *@@%        -%@@@@@@@@@@@@@@@#       @@@%      @@       .               
                  %       +@@+       %@@@@@@#+-     :+%@@@@@%      @@@.     %@       =              
                 @       @@#      *@@@@@                 -@@@@@     %@@:     @@       .             
               .*      -@@      %@@@@       .@@@@@@@@@      @@@@+    @@@=     @%      =             
               *      *@@     +@@@#     :@@@@@@@@@@@@@@@@    =@@@-    @@@     -#                    
              @      :*=     %@@@     %@@@@@@:       @@@@@+   +@@@    :@@+     *+      :            
             +      .@@     @@@%    *@@@@*             @@@@:   @@@@    @@@     @@      =            
             +      @@     %@@%    @@@@%    :@@@@@@@@@@@@@@+   @@@@    @@@     @@      =            
            .      -@*    .@@@    %@@@.   You have been called  @@@@+   @@@@    @@@     @@                  
            -      @@     *@@    :@@@=  You have been selected @@@*    @@%     @@      =            
            =      @@     @@@    @@@@   You have been chosen @@@@    %@@=    -@#      :            
            =      @@     @@@    @@@@   =@@@@@@@@@@@@@@#    =@@@@    =@@@     @@      =             
            -      @@     @@@    @@@@   .@@@@    ..       :@@@@@    =@@@     @@=      #             
            .      #@     =@@-    @@@*   +@@@@#        =@@@@@@     *@@@     +@@      @              
                    @*     @@@    -@@@=    @@@@@@@@@@@@@@@@%     -@@@@     +@@      =               
             =      %@     -@@@    +@@@@     .@@@@@@@@@%       *@@@@      @@#      :=               
                     @@     :@@@     @@@@@                  +@@@@@      :@@-      *+                
              =       @%     .@@@      @@@@@@*:       .=#@@@@@@=       #@#       #                  
               :       @@      @@@@      -@@@@@@@@@@@@@@@@@#        .%%+        @                   
                -       @@       @@@@          -#%%#+            .@@@@        @:                    
                 =       =@%       %@@@@:                     @@@@@         @*                      
                           @@*        +@@@@@@#+      .=#%@@@@@@.          @=                        
                    .        *@%          .=@@@@@@@@@@@@#-.            #@                           
                                @@#                                .@@.                             
                                   %@@+                        +@@=                                 
                                       :@@@@@@#=-::=*%@@@@@*                                      
                                                                                                                          

  
                        The Enlightened Ones have deemed you a Guardian of Sol.

                                
                                     You are the {final_title}!


                            Bring forth your power, wisdom, and courage.   

                                      Bring forth your light.

                        It is now your duty to protect the light of creation.

                                        Others will join.


                                        
                                        I am here for you all,

                                                Maia




    """

    print_path = os.path.join(STATIC_AUDIO_DIR, "certificate.txt")
    with open(print_path, "w") as f:
        f.write(certificate_text)

    #print that shit
    print_certificate_text(certificate_text, user_name=user_name)

### i am sure there is a better way to fade out the music
    await asyncio.sleep(40)
    osc_client.send_message("/audio/volume/", -12)
    await asyncio.sleep(2)
    osc_client.send_message("/audio/volume/", -24)
    await asyncio.sleep(2)
    osc_client.send_message("/audio/volume/", -36)
    await asyncio.sleep(2)
    osc_client.send_message("/audio/volume/", -48)

    # Lights cue
    lighting_cues = {
        "maiaLEDmode": 0,
        "floor": 1,
        "floor2": 1,
        "floor3": 1,
        "desk": 1,
        "projector": 0,
    }
    for light, value in lighting_cues.items():
        osc_client.send_message(f"/lighting/{light}", value)

    #the show is now complete
    print("🌌 SHOW IS COMPLETE - CLICK RESTART")    
    return {"message": "Phase 5 - Departure completed."}
