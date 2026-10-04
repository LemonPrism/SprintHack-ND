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
import html
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
    "Groq (free, gpt-oss-120B)": ("groq", "openai/gpt-oss-120b"),
    "From .env": (None, None),
}

# --- styling -----------------------------------------------------------------
# Subtle, professional. A slate/indigo palette, quiet surfaces, one accent.
_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap');

:root {
  --ps-ink: #0f172a;
  --ps-muted: #64748b;
  --ps-line: #e2e8f0;
  --ps-surface: #ffffff;
  --ps-ground: #f7f8fa;
  --ps-accent: #4f46e5;
  --ps-ok: #0f9d6b;
  --ps-warn: #c2770b;
  --ps-channel: #b4530f;
}

html, body, [class*="css"] { font-family: 'Inter', system-ui, -apple-system, sans-serif; }
.stApp { background: var(--ps-ground); }
.block-container { padding-top: 2.4rem; max-width: 1180px; }

/* Header */
.ps-title { font-size: 1.9rem; font-weight: 700; letter-spacing: -0.02em;
  color: var(--ps-ink); margin: 0; display: flex; align-items: center; gap: .55rem; }
.ps-dot { width: 11px; height: 11px; border-radius: 50%; background: var(--ps-accent);
  box-shadow: 0 0 0 4px rgba(79,70,229,.15); }
.ps-tagline { color: var(--ps-muted); font-size: .95rem; margin: .35rem 0 0;
  max-width: 62ch; line-height: 1.5; }
.ps-rule { height: 1px; background: var(--ps-line); border: 0; margin: 1.3rem 0 1.5rem; }

/* Input label */
.ps-eyebrow { text-transform: uppercase; letter-spacing: .08em; font-size: .72rem;
  font-weight: 600; color: var(--ps-muted); margin-bottom: .4rem; }

/* Text area / inputs */
.stTextArea textarea, .stTextInput input {
  border-radius: 10px !important; border: 1px solid var(--ps-line) !important;
  background: var(--ps-surface) !important; font-size: .95rem !important;
  color: var(--ps-ink) !important; box-shadow: none !important;
}
.stTextArea textarea:focus, .stTextInput input:focus {
  border-color: var(--ps-accent) !important;
  box-shadow: 0 0 0 3px rgba(79,70,229,.12) !important;
}

/* Primary button */
.stButton > button {
  border-radius: 10px; font-weight: 600; padding: .55rem 1.1rem;
  border: 1px solid transparent; transition: transform .04s ease, filter .15s ease;
}
.stButton > button[kind="primary"] { background: var(--ps-accent); }
.stButton > button[kind="primary"]:hover { filter: brightness(1.07); }
.stButton > button[kind="primary"]:active { transform: translateY(1px); }

/* Sidebar */
section[data-testid="stSidebar"] { background: var(--ps-surface);
  border-right: 1px solid var(--ps-line); }
section[data-testid="stSidebar"] .stSelectbox label,
section[data-testid="stSidebar"] .stRadio label,
section[data-testid="stSidebar"] .stTextInput label { font-weight: 500; }

/* Result panes */
.ps-pane { background: var(--ps-surface); border: 1px solid var(--ps-line);
  border-radius: 14px; padding: 1.05rem 1.15rem; height: 100%;
  box-shadow: 0 1px 2px rgba(15,23,42,.04); }
.ps-pane-head { display: flex; align-items: center; justify-content: space-between;
  gap: .5rem; margin-bottom: .7rem; }
.ps-pane-label { font-size: .82rem; font-weight: 600; color: var(--ps-ink); }
.ps-pane-label .n { color: var(--ps-muted); font-weight: 700; margin-right: .3rem; }
.ps-chip { font-size: .68rem; font-weight: 600; letter-spacing: .03em;
  padding: .16rem .5rem; border-radius: 999px; white-space: nowrap; }
.ps-chip.ink { background: #eef1f6; color: var(--ps-muted); }
.ps-chip.channel { background: #fdf0e6; color: var(--ps-channel); }
.ps-chip.ok { background: #e6f6ef; color: var(--ps-ok); }
.ps-chip.warn { background: #fdf3e3; color: var(--ps-warn); }
.ps-msg { font-size: .95rem; line-height: 1.55; color: var(--ps-ink);
  overflow-wrap: anywhere; }
.ps-msg.mono { font-family: 'JetBrains Mono', ui-monospace, monospace;
  font-size: .86rem; }
.ps-note { margin-top: .7rem; font-size: .78rem; color: var(--ps-muted);
  line-height: 1.45; border-top: 1px dashed var(--ps-line); padding-top: .6rem; }
</style>
"""


@st.cache_data
def load_examples() -> dict[str, str]:
    try:
        with open(CASES_PATH, encoding="utf-8") as f:
            return {c["id"]: c["secret"] for c in json.load(f)}
    except Exception:
        return {}


def pane(col, *, n: str, label: str, chip_class: str, chip_text: str,
         body: str, mono: bool = False, note: str | None = None) -> None:
    note_html = f'<div class="ps-note">{note}</div>' if note else ""
    col.markdown(
        f'<div class="ps-pane">'
        f'  <div class="ps-pane-head">'
        f'    <span class="ps-pane-label"><span class="n">{n}</span>{html.escape(label)}</span>'
        f'    <span class="ps-chip {chip_class}">{html.escape(chip_text)}</span>'
        f'  </div>'
        f'  <div class="ps-msg {"mono" if mono else ""}">{html.escape(body)}</div>'
        f'  {note_html}'
        f'</div>',
        unsafe_allow_html=True,
    )


def main() -> None:
    st.set_page_config(page_title="PlainSight", page_icon="📨", layout="wide",
                       initial_sidebar_state="expanded")
    st.markdown(_CSS, unsafe_allow_html=True)

    st.markdown(
        '<h1 class="ps-title"><span class="ps-dot"></span>PlainSight</h1>'
        '<p class="ps-tagline">A generative codebook: hide a sensitive message inside '
        'ordinary chatter, send it over an open channel, and recover it on the other '
        'side. Use the sidebar (collapse it with «) to pick the model, codec, theme, '
        'and keys.</p>'
        '<hr class="ps-rule">',
        unsafe_allow_html=True,
    )

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

    st.markdown('<div class="ps-eyebrow">① The sender\'s real (clandestine) message</div>',
                unsafe_allow_html=True)
    secret = st.text_area(
        "secret", key="secret", label_visibility="collapsed",
        value=st.session_state.get("secret", ""), height=120,
        placeholder="Type the sensitive message to protect…",
    )

    go = st.button("Send through PlainSight  →", type="primary",
                   disabled=not secret.strip(), use_container_width=True)

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

        st.markdown('<div style="height:.4rem"></div>', unsafe_allow_html=True)
        c1, c2, c3 = st.columns(3, gap="medium")

        pane(c1, n="①", label="Sender sees", chip_class="ink",
             chip_text="the secret", body=secret)

        seen = stego.visible(cover)
        hidden = len(cover) - len(seen)
        if hidden:
            note = (f"🔒 {hidden} invisible characters carry the entire encrypted "
                    f"message — unreadable without the key. The eye sees only chatter.")
        else:
            note = "No operational words — it reads like ordinary chatter."
        pane(c2, n="②", label="Open channel sees", chip_class="channel",
             chip_text="intercepted", body=seen, note=note)

        exact = recovered.strip() == secret.strip()
        pane(c3, n="③", label="Receiver recovers",
             chip_class="ok" if exact else "warn",
             chip_text="exact match" if exact else "≈ usable",
             body=recovered,
             note=None if exact else "Recovered close enough to be usable.")

        if receiver_key != sender_key:
            st.markdown('<div style="height:.6rem"></div>', unsafe_allow_html=True)
            st.info("Receiver key differs from sender key — for the keyed codec the "
                    "payload will not decode. That's the point: the model alone isn't enough.")


if __name__ == "__main__":
    main()
