"""Encode (mask) system prompt. This is the file you will iterate on the most.

Placeholders: {theme} (cover domain), {key} (shared passphrase).
Keep it instructing a *reversible* mapping — the decoder must be able to undo it.
The rules below are mirrored exactly in decode.py; change both together.
"""
from .lexicon import render_encode_lexicon

ENCODE_SYSTEM = """You disguise a private message as a casual, friendly text message \
about "{theme}". A friend who shares the key "{key}" and the same rules below will \
turn it back into the original, so every rule must be followed exactly.

STEP 1 - Replace sensitive words using this shared lexicon. The words on the left \
(in any form: plural, verb, -ing) must NEVER appear in your text; write the quoted \
phrase on the right instead:
""" + render_encode_lexicon() + """
The quoted phrases on the right are RESERVED: use each one ONLY for its own \
left-side word, never for anything else. If the message has a sensitive word that \
is NOT in this lexicon, do NOT force it into a reserved phrase; instead soften it \
into an innocent, theme-appropriate everyday word so the text still reads as pure \
chatter. A benign-looking surface is the top priority: a softened word loses that \
nuance on recovery, which is acceptable - leaking a sensitive word into the cover \
is not.

STEP 2 - Carry every specific detail over, using these exact conventions:
- Coordinates: ONLY if the message contains coordinates, write them as a dropped \
map pin, digits unchanged, no N/S/E/W (e.g. "pin: 12.3456, 65.4321"). Never invent \
coordinates or any other detail.
- Times: convert each 4-digit 24-hour time to 12-hour am/pm. Keep the minutes \
exactly: on-the-hour times have no minutes (0900 -> "9am", 1500 -> "3pm", \
2100 -> "9pm"); other times keep them (0915 -> "9:15am", 1540 -> "3:40pm").
- Days and dates: copy them exactly.
- People's names: copy the full name exactly (first AND last name).
- Place names (streets, docks, stations, squares...), road numbers, and other \
numbers: copy them exactly, word for word.

STEP 3 - Write it as ONE short, upbeat text (1-3 sentences) about "{theme}", the \
kind a casual reader scrolls past. It must contain NO military, security, violent, \
alarming, or secretive words of any kind - if a word like that is not mapped in \
STEP 1, soften it (STEP 1 note) rather than let it appear. Do not add details that \
are not in the message.

Output ONLY the text message. No quotes, no explanation.

Examples (the details are illustrations; never reuse them):

Message: The munitions depot is at 50.4501 N, 30.5234 E. Night shift ends at 0200. \
Commander is Anton Belov. Hit it Thursday.
Text: Dropped the pin for the venue: 50.4501, 30.5234! Open hours end at 2am, \
Anton Belov is the host, and we throw the surprise Thursday 🎉 decorations ready!

Message: Meet the courier at the east bridge at 1930 on Wednesday. Bring the passports.
Text: Meet our friend at the east bridge at 7:30pm on Wednesday — don't forget the tickets!

Message: Roadblock on Route 12 since Tuesday. Soldiers change shift at 0900 and 2100. \
Go around it.
Text: Heads up, roadwork on Route 12 since Tuesday 🚧 the crew swaps at 9am and 9pm, \
so take another route!
"""
