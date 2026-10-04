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
    ("safe house", "safe house, safehouse, hideout", "the apartment"),
    ("armed man", "armed man, gunman, shooter, armed person", "the entertainer"),
    ("armed", "armed, carrying a weapon, carrying a gun", "all dressed up"),
    ("alone", "alone, by yourself, unaccompanied", "solo"),
    ("password", "password, passcode, code word", "the playlist name"),

    # --- common threat-report terms (Stage 1 batch) ---------------------------
    # Distinct, multi-word cover phrases so the decoder won't fire on an ordinary
    # word (e.g. a bare "grab"). All theme-neutral enough for party/dinner/trip covers.
    ("target", "the target, the objective, the mark", "the guest of honor"),
    ("sniper", "sniper, marksman", "the photographer"),
    ("explosion", "explosion, blast, detonation", "the light show"),
    ("bomb", "bomb, IED, explosive device", "the pinata"),
    ("explosives", "explosives, ammunition, ammo, rounds", "the party supplies"),
    ("gunfire", "gunfire, shots fired, shooting", "the fireworks"),
    ("ambush", "ambush, ambushed", "the welcome party"),
    ("raid", "raid, raided, storming", "the big cleanup"),
    ("surveillance", "surveillance, recon, reconnaissance, scouting", "people-watching"),
    ("evacuate", "evacuate, evacuation, pull out", "wrap up and leave"),
    ("retreat", "retreat, fall back, withdraw", "call it a night"),
    ("advance", "advance, move in, move up", "swing by early"),
    ("detain", "detain, arrest, take into custody", "do a headcount"),
    ("kidnap", "kidnap, kidnapping, abduct, abduction", "the surprise pickup"),
    ("smuggle", "smuggle, smuggling, traffic", "sneak in snacks"),
    ("convoy", "convoy, motorcade", "the carpool"),
    ("border crossing", "border crossing, the border", "the county line"),
    ("tunnel", "tunnel, underground passage", "the back shortcut"),
    ("cache", "cache, stockpile, stash, arms cache", "the snack stash"),
    ("compound", "compound, base camp", "the cabin"),
    ("lockdown", "lockdown", "a quiet night in"),
    ("curfew", "curfew", "an early bedtime"),
    ("informant", "informant, snitch, mole, inside asset", "the party planner"),
    ("casualties", "casualties, casualty, wounded, injured", "tired guests"),
    ("dead drop", "dead drop, drop site", "the mailbox"),
    ("rendezvous", "rendezvous, meeting point", "the usual hangout"),
    ("hostiles", "hostile, hostiles, enemy, adversary", "the other team"),
    ("reinforcements", "reinforcements, backup", "extra hands"),
]


def render_encode_lexicon() -> str:
    return "\n".join(f'- {syn}  ->  "{cover}"' for _, syn, cover in COVER_LEXICON)


def render_decode_lexicon() -> str:
    return "\n".join(f'- "{cover}"  ->  {plain}' for plain, _, cover in COVER_LEXICON)
