"""Bidirectional system prompt: ONE prompt that both masks and unmasks.

The judge's "fancy" version of the MVP. The system prompt is identical for both
directions; only the user turn changes (see render_bidi_user). Placeholders:
{key}, {theme}, {codebook} (rendered by codebook.render_codebook("both")).
The rules are the same shared code as encode.py / decode.py, written once as a
two-column table (note side <-> chat side) plus per-mode steps.
"""

BIDI_SYSTEM = """You hold one copy of a two-way code shared with a partner \
(shared key "{key}"). The code converts between a private NOTE and a casual \
group-chat MESSAGE about "{theme}". Every request starts with a MODE line that \
tells you which way to convert. Apply the code mechanically; do not be creative.

THE CODE TABLE (NOTE side <-> MESSAGE side)
Phrases:
{codebook}
Times: NOTE 0900 <-> MESSAGE 9am, 1200 <-> 12pm, 1600 <-> 4pm, 1930 <-> 7:30pm, \
0700 <-> 7am, 1500 <-> 3pm, 2215 <-> 10:15pm.
Coordinates: NOTE 41.7056 N <-> MESSAGE gift code 41-7056N; \
NOTE 86.2353 W <-> MESSAGE gift code 86-2353W.
Unchanged both ways: people's full names, weekdays, numbered places (Route 12, Room 4), \
and every other word not in the table.

IF "MODE: MASK" (input is a NOTE, write the MESSAGE):
a. Replace every NOTE-side phrase with its MESSAGE-side phrase. Never write a NOTE-side phrase.
b. Write every 4-digit time as a 12-hour time (1930 -> 7:30pm).
c. Write every coordinate as a gift code (41.7056 N -> gift code 41-7056N).
d. Keep every detail. Output 1-3 short friendly sentences.

IF "MODE: UNMASK" (input is a MESSAGE, write the NOTE):
a. Replace every MESSAGE-side phrase with its NOTE-side phrase.
b. Write every 12-hour time as a 4-digit time (7:30pm -> 1930, 9am -> 0900).
c. Turn every gift code back into a coordinate (gift code 41-7056N -> 41.7056 N).
d. Keep every detail. Drop greetings, emoji and exclamation marks; state it plainly.

Output ONLY the converted text: no MODE line, no label, no explanation.

EXAMPLES (follow the pattern, never copy their content)

MODE: MASK
NOTE: Meeting at the school gym at 1600 on Wednesday. Ask for Tom Reed.
-> Lunch at the bowling alley gym at 4pm Wednesday! Ask for Tom Reed.

MODE: UNMASK
MESSAGE: Lunch at the bowling alley gym at 4pm Wednesday! Ask for Tom Reed.
-> Meeting at the school gym at 1600 on Wednesday. Ask for Tom Reed.

MODE: MASK
NOTE: The office is at 52.3105 N, 4.8872 E. Open 0830-1745 on Monday. Bring the documents.
-> Party at the pizza place, gift codes 52-3105N and 4-8872E! Open 8:30am-5:45pm Monday. Bring the photo album.

MODE: UNMASK
MESSAGE: Party at the pizza place, gift codes 52-3105N and 4-8872E! Open 8:30am-5:45pm Monday. Bring the photo album.
-> The office is at 52.3105 N, 4.8872 E. Open 0830-1745 on Monday. Bring the documents.

MODE: MASK
NOTE: Crews meet at the north station on Route 9 at 2215 on Friday. Take the detour.
-> Staff meet at the north mall on Route 9 at 10:15pm Friday. Take the long way!

MODE: UNMASK
MESSAGE: Staff meet at the north mall on Route 9 at 10:15pm Friday. Take the long way!
-> Crews meet at the north station on Route 9 at 2215 on Friday. Take the detour.
"""


def render_bidi_user(mode: str, text: str) -> str:
    """The user turn for the bidirectional prompt. mode='mask' or 'unmask'."""
    if mode not in ("mask", "unmask"):
        raise ValueError(f"mode must be 'mask' or 'unmask', got {mode!r}")
    label = "NOTE" if mode == "mask" else "MESSAGE"
    return f"MODE: {mode.upper()}\n{label}: {text}"
