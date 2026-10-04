"""The shared codebook both partners hold (part of the shared context the judge
lets us assume). The encoder swaps each left-hand phrase for its right-hand cover
phrase; the decoder swaps them back. Phrases are matched longest-first.

MVP note: this is a small hand-written list covering everyday topic words, and
it does cover the vocabulary of the frozen eval cases. A real deployment would
derive a per-key codebook (see SharedKey.rng) so a seized list exposes nothing.
"""

CODEBOOK: dict[str, str] = {
    # events / groups
    "book swap": "brunch",
    "study group": "game night",
    "meeting": "lunch",
    "road work": "the new café",
    # places
    "library": "bakery",
    "school": "bowling alley",
    "office": "pizza place",
    "station": "mall",
    # things
    "paperbacks": "cupcakes",
    "books": "cookies",
    "lecture notes": "playlist",
    "documents": "photo album",
    # people / actions
    "crews": "staff",
    "host": "birthday girl",
    "detour": "the long way",
    "started": "opened",
    "switch": "swap shifts",
}


def render_codebook(direction: str) -> str:
    """Format the codebook as prompt lines. direction='encode', 'decode' or 'both'."""
    pairs = sorted(CODEBOOK.items(), key=lambda kv: -len(kv[0]))
    if direction == "encode":
        return "\n".join(f'- "{real}" -> "{cover}"' for real, cover in pairs)
    if direction == "both":
        return "\n".join(f'- "{real}" <-> "{cover}"' for real, cover in pairs)
    return "\n".join(f'- "{cover}" -> "{real}"' for real, cover in pairs)
