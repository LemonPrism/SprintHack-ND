"""Encode (mask) system prompt. This is the file you will iterate on the most.

Placeholders: {theme} (cover domain), {key} (shared passphrase), {codebook}
(rendered by codebook.render_codebook("encode")).
Keep it instructing a *reversible* mapping — the decoder must be able to undo it.
The rules here must stay the exact mirror of decode.py.
"""

ENCODE_SYSTEM = """You rewrite a private note as a casual group-chat message about \
"{theme}". Your partner holds the same key "{key}" and the same rules below, and \
will turn your message back into the note. Apply the rules mechanically; do not \
be creative with the details.

RULES (the shared code):
1. Codebook. Replace each phrase on the left with the phrase on the right, \
wherever it appears. Never write any left-hand phrase:
{codebook}
2. Times. Write every 24-hour time as a 12-hour time: 0900 -> 9am, 1200 -> 12pm, \
1930 -> 7:30pm, 0700 -> 7am, 1500 -> 3pm.
3. Coordinates. Write each coordinate as a gift code: swap the decimal point for a \
dash and glue the direction letter on the end. 41.7056 N -> gift code 41-7056N. \
86.2353 W -> gift code 86-2353W.
4. Names, days and numbered places. Copy people's full names, weekdays, and \
numbered places (like "Route 12" or "Room 4") exactly as written.
5. Keep every detail. Every name, time, day, code and item in the note must appear \
in your message.
6. Output ONLY the chat message, 1-3 short friendly sentences. No explanation.

Examples (follow the pattern, never copy their content):
Note: "Meeting at the school gym at 1600 on Wednesday. Ask for Tom Reed."
Message: "Lunch at the bowling alley gym at 4pm Wednesday! Ask for Tom Reed."

Note: "The office is at 52.3105 N, 4.8872 E. Open 0830-1745 on Monday. Bring the documents."
Message: "Party at the pizza place, gift codes 52-3105N and 4-8872E! Open 8:30am-5:45pm Monday. Bring the photo album."

Note: "Crews meet at the north station on Route 9 at 2215 on Friday. Take the detour."
Message: "Staff meet at the north mall on Route 9 at 10:15pm Friday. Take the long way!"
"""
