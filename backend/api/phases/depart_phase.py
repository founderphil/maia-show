"""
Phase 5 - Departure
34. Light cue 6
        MAIA LED - addressable : color gold mixed with purple. All led lights are flickering.
        HOUSE LIGHT 1 : ON flicker 10% to 50%
        HOUSE LIGHT 2 : ON flicker 10% to 50%
        CHAIR SPOT : OFF
        MAIA SPOT 1 : ON flicker 10% to 50%
        MAIA SPOT 2 : ON flicker 10% to 50%
        MAIA PROJECTOR 1 : OFF
        MAIA PROJECTOR 2 : OFF
35. Play DEPARTURE.WAV
36. START “GUARDIAN” Pipeline
-Load LLM model with knowledge of celestial and terrestrial objects 
-Send LLM assignment.themes_1 + assignment.themes_2 + assignment.themes_3 + “Uses a zero-shot classification pipeline to infer the most likely theme.”
-Save assigned location to profile_data.guardian_assignment 
37. Light cue 1 [return to cue 1 for next guest]
38. Play music MAJO.WAV at 100% volume
39. Process text to send to printer connected in the room.
        <name>. 
        IT IS WITH HONOR THAT YOU ARE A GUARDIAN OF SOL.
        GO FORTH GUARDIAN. YOUR ANSWERS HAVE DEEMED YOU THE PROTECTOR OF SOL OF THE <profile_data.guardian_assignemnt>. 
        SPREAD YOUR LIGHT TO OTHERS - TEAR THE BOTTOM OF THIS MESSAGE AND WRITE YOUR OWN TO INSPIRE OTHER GUARDIANS OF SOL.
        WE SHALL MEET AGAIN.
        MAIA
        —------------------------
        Send data to printer. Print.
        
40. POSTSHOW Post show data permissions sends data to a cloud to create a user and save selected data from a list.

"""