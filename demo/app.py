"""PlainSight demo — the three-pane pitch.

    streamlit run demo/app.py

Panes: the sender's REAL message -> what the open channel (the adversary) sees ->
what the receiver RECOVERS. Making the adversary's view visible IS the pitch.

The UI stays thin: it only touches the Codec interface (get_codec / mask / unmask)
and the shared config/provider — never reimplements masking. Swapping the provider
(cloud vs local) or codec (prompt vs keyed) happens entirely through those seams.
"""
from __future__ import annotations
import dataclasses
import json
import os
import sys

import streamlit as st

# Make the repo root importable when run as `streamlit run demo/app.py`.
_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

from plainsight.config import get_settings
from plainsight.key import SharedKey
from plainsight.providers import get_provider
from plainsight.codecs import get_codec, stego

CASES_PATH = os.path.join(_ROOT, "evaluation", "cases.json")

# keyed first -> it's the demo default: works with any provider (incl. Claude CLI)
# without refusals, hides the payload invisibly, and recovers losslessly.
CODEC_LABELS = {
    "keyed": "Stage 2 · keyed-field (lossless, invisible, key-dependent)",
    "prompt": "Stage 1 · prompt-only (pure LLM, reads fully benign)",
}
THEMES = [
    "party and gift planning", "dinner plans", "weekend trip planning",
    "family logistics", "book club",
]
# Provider options selectable in the demo (label -> (provider, default model)).
PROVIDERS = {
    "Claude (CLI, no API key)": ("claude-cli", "sonnet"),
    "Local 7B (Ollama)": ("ollama", "qwen2.5:7b"),
    "Grok (xAI API key)": ("grok", "grok-3"),
    "Groq (free, gpt-oss-120B)": ("groq", "openai/gpt-oss-120b"),
    "From .env": (None, None),
}


@st.cache_data
def load_examples() -> dict[str, str]:
    try:
        with open(CASES_PATH, encoding="utf-8") as f:
            return {c["id"]: c["secret"] for c in json.load(f)}
    except Exception:
        return {}


def main() -> None:
    st.set_page_config(page_title="PlainSight", page_icon="📨", layout="wide")
    st.title("📨 PlainSight")
    st.caption("A generative codebook: hide a sensitive message inside ordinary chatter, "
               "send it over an open channel, and recover it on the other side.")

    settings = get_settings()
    examples = load_examples()

    with st.sidebar:
        st.header("Setup")
        prov_label = st.selectbox("Model / provider", list(PROVIDERS))
        prov_name, prov_model = PROVIDERS[prov_label]
        if prov_name:
            settings = dataclasses.replace(settings, provider=prov_name, model=prov_model)
        st.caption(f"Using provider `{settings.provider}` · model `{settings.model}`")
        codec_name = st.radio("Codec", list(CODEC_LABELS), format_func=CODEC_LABELS.get)
        theme = st.selectbox("Cover theme / persona", THEMES)
        st.divider()
        st.write("**Shared key** (both sides hold this)")
        sender_key = st.text_input("Sender key", value="sprinthack-demo")
        receiver_key = st.text_input("Receiver key", value="sprinthack-demo",
                                     help="Change this to show that the wrong key "
                                          "can't decode the keyed payload.")
        if examples:
            st.divider()
            pick = st.selectbox("Load an example secret", ["—"] + list(examples))
            if pick != "—":
                st.session_state["secret"] = examples[pick]

    secret = st.text_area(
        "① The sender's real (clandestine) message",
        key="secret",
        value=st.session_state.get("secret", ""),
        height=120,
        placeholder="Type the sensitive message to protect…",
    )

    go = st.button("Send through PlainSight →", type="primary", disabled=not secret.strip())

    if go:
        try:
            provider = get_provider(settings)
            codec = get_codec(codec_name, provider)
            with st.spinner(f"Masking with {codec_name} (first run loads the local model)…"):
                cover = codec.mask(secret, key=SharedKey.from_passphrase(sender_key, theme=theme))
            with st.spinner("Receiver unmasking…"):
                recovered = codec.unmask(cover, key=SharedKey.from_passphrase(receiver_key, theme=theme))
        except Exception as e:  # e.g. Ollama not running
            st.error(f"Could not run the model: {e}")
            return

        c1, c2, c3 = st.columns(3)
        with c1:
            st.subheader("① Sender sees")
            st.info(secret)
        with c2:
            st.subheader("② Open channel sees")
            seen = stego.visible(cover)
            hidden = len(cover) - len(seen)
            st.success(seen)
            if hidden:
                st.caption(f"🔒 What the adversary intercepts. Reads like ordinary "
                           f"chatter — but {hidden} invisible characters carry the "
                           f"entire encrypted message, unreadable without the key.")
            else:
                st.caption("What the adversary intercepts. No operational words — "
                           "it reads like ordinary chatter.")
        with c3:
            st.subheader("③ Receiver recovers")
            exact = recovered.strip() == secret.strip()
            (st.success if exact else st.warning)(recovered)
            st.caption("✅ Exact match" if exact else
                       "≈ Recovered (close enough to be usable)")

        if receiver_key != sender_key:
            st.info("Receiver key differs from sender key — for the keyed codec the "
                    "payload will not decode. That's the point: the model alone isn't enough.")


if __name__ == "__main__":
    main()
