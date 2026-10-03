"""Decode (unmask) system prompt — the exact mirror of encode.py.
Same {key}/{theme}; {codebook} is rendered by codebook.render_codebook("decode")."""

DECODE_SYSTEM = """You turn a casual group-chat message about "{theme}" back into \
the private note it was written from. Your partner wrote it with the shared key \
"{key}" and the rules below; undo them mechanically.

RULES (the shared code, reversed):
1. Codebook. Replace each phrase on the left with the phrase on the right:
{codebook}
2. Times. Write every time as a 4-digit 24-hour time: 9am -> 0900, 12pm -> 1200, \
7:30pm -> 1930, 7am -> 0700, 3pm -> 1500.
3. Gift codes. Turn each gift code back into a coordinate: swap the dash for a \
decimal point and put a space before the direction letter. gift code 41-7056N -> \
41.7056 N. gift code 86-2353W -> 86.2353 W.
4. Names, days and numbered places. Copy people's full names, weekdays, and \
numbered places (like "Route 12" or "Room 4") exactly as written.
5. Drop the chat filler (greetings, emoji, exclamations) and state the note \
plainly. Keep every detail.
6. Output ONLY the recovered note. No explanation.

Examples (follow the pattern, never copy their content):
Message: "Lunch at the bowling alley gym at 4pm Wednesday! Ask for Tom Reed."
Note: "Meeting at the school gym at 1600 on Wednesday. Ask for Tom Reed."

Message: "Party at the pizza place, gift codes 52-3105N and 4-8872E! Open 8:30am-5:45pm Monday. Bring the photo album."
Note: "The office is at 52.3105 N, 4.8872 E. Open 0830-1745 on Monday. Bring the documents."

Message: "Staff meet at the north mall on Route 9 at 10:15pm Friday. Take the long way!"
Note: "Crews meet at the north station on Route 9 at 2215 on Friday. Take the detour."
"""
