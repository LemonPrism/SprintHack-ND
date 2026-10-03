"""The shared cover lexicon: sensitive concept -> innocent stand-in.

Both endpoints render the SAME table into their prompts, which is what makes the
mapping reversible. It is part of the shared context the judge said we may
assume. Each entry is (plain word the decoder writes back, synonyms the encoder
must hide, cover phrase). Keep cover phrases distinctive (one meaning each) and
theme-neutral enough to fit most covers. Synonyms collapse to the plain word on
decode — a known, acceptable loss. Later this table can be key-derived (see
ARCHITECTURE.md, "Key separation").
"""

COVER_LEXICON: list[tuple[str, str, str]] = [
    ("facility", "factory, plant, depot, base, site, facility", "the venue"),
    ("weapons", "drones, weapons, munitions, missiles", "decorations"),
    ("destroy it", "destroy, strike, attack, hit, bomb", "throw the surprise"),
    ("extraction point", "extraction point, pickup point", "the meetup spot"),
    ("documents", "documents, files, papers", "the photo album"),
    ("passports", "passports, IDs", "the tickets"),
    ("checkpoint", "checkpoint, roadblock", "roadwork"),
    ("guards", "guards, soldiers, police", "the crew"),
    ("patrol", "patrol, patrols, patrolling (the verb)", "hangs out on"),
    ("guards rotate", "guards rotate, shift change, change shift", "the crew swaps"),
    ("avoid it", "avoid, stay away, go around", "take another route"),
    ("workday", "workday, operating hours, working hours", "open hours"),
    ("commander", "plant manager, commander, officer in charge", "the host"),
    ("handler", "courier, handler, contact", "our friend"),
]


def render_encode_lexicon() -> str:
    return "\n".join(f'- {syn}  ->  "{cover}"' for _, syn, cover in COVER_LEXICON)


def render_decode_lexicon() -> str:
    return "\n".join(f'- "{cover}"  ->  {plain}' for plain, _, cover in COVER_LEXICON)
