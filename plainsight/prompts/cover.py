"""Cover prompt for the keyed codec.

The keyed codec does NOT need the visible text to carry any information — the secret
rides in the invisible payload. So this prompt asks for a totally generic, specific-
free message. The secret is never shown to the model, so it cannot leak into the cover.
"""

COVER_SYSTEM = """You write ONE short, friendly, utterly ordinary text message about \
"{theme}" — the kind of throwaway message anyone sends a friend.

Hard rules:
- Include NO specific numbers, times, dates, names, places, coordinates, or instructions.
- No urgent, secretive, violent, security, or operational wording of any kind.
- One short sentence. At most one emoji.

Output ONLY the message text. No quotes, no explanation."""
