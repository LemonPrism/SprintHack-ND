"""Stage 3 — three-pane live demo.

    streamlit run demo/app.py

Sender's real message | what an eavesdropper sees | receiver's recovered message.
Thin UI: it only calls the Codec interface (plus a labelled replay of recorded
real model output in demo/sample_data.json in case the model is down mid-pitch).
"""
from __future__ import annotations
import html
import json
import os
import sys
import time

import streamlit as st

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from plainsight.config import get_settings          # noqa: E402
from plainsight.key import SharedKey                # noqa: E402
from plainsight.providers import get_provider       # noqa: E402
from plainsight.codecs import get_codec             # noqa: E402
from plainsight.prompts import CODEBOOK             # noqa: E402

SAMPLES_PATH = os.path.join(ROOT, "demo", "sample_data.json")
CASES_PATH = os.path.join(ROOT, "evaluation", "cases.json")
THEMES = ["party and gift planning", "weekend sports chat", "family group text", "dinner plans"]
CODECS = {
    "bidi": "One bidirectional prompt",
    "prompt": "Two prompts (encode / decode)",
}

CSS = """
<style>
:root {
  --bg: #0A0F1C; --panel: #111827; --panel-2: #0D1424; --line: #1E2A40;
  --text: #E8ECF4; --muted: #8B97AE; --faint: #5B6780;
  --amber: #F5B544; --blue: #3B82F6; --teal: #2DD4A7; --red: #F2555A;
}
.stApp { background: radial-gradient(1200px 600px at 10% -10%, #14213D 0%, var(--bg) 55%); }
.block-container { padding-top: 2.2rem; max-width: 1280px; }
header[data-testid="stHeader"] { background: transparent; }
section[data-testid="stSidebar"] { background: var(--panel-2); border-right: 1px solid var(--line); }

.ps-hero { display: flex; align-items: flex-end; justify-content: space-between;
  gap: 1.5rem; flex-wrap: wrap; margin-bottom: 1.4rem; }
.ps-brand { display: flex; align-items: center; gap: .85rem; }
.ps-mark { width: 46px; height: 46px; border-radius: 12px;
  background: linear-gradient(135deg, var(--amber), var(--teal));
  display: grid; place-items: center; box-shadow: 0 8px 30px rgba(45,212,167,.18); }
.ps-mark span { width: 18px; height: 18px; border-radius: 50%; background: var(--bg);
  box-shadow: 0 0 0 4px rgba(10,15,28,.35); }
.ps-title { font-size: 2.1rem; font-weight: 750; letter-spacing: -.02em; color: var(--text); line-height: 1; }
.ps-sub { color: var(--muted); font-size: 1rem; margin-top: .35rem; max-width: 640px; }
.ps-pills { display: flex; gap: .5rem; flex-wrap: wrap; }
.ps-pill { border: 1px solid var(--line); background: rgba(17,24,39,.7); color: var(--muted);
  border-radius: 999px; padding: .3rem .75rem; font-size: .8rem; }
.ps-pill b { color: var(--text); font-weight: 600; }
.ps-dot { display: inline-block; width: 7px; height: 7px; border-radius: 50%; margin-right: .4rem;
  background: var(--teal); vertical-align: middle; }
.ps-dot.off { background: var(--amber); }

.ps-card { background: var(--panel); border: 1px solid var(--line); border-radius: 16px;
  padding: 1.1rem 1.2rem 1.2rem; min-height: 400px; position: relative; overflow: hidden; }
.ps-card::before { content: ""; position: absolute; inset: 0 0 auto 0; height: 3px; background: var(--accent); }
.ps-card.sender { --accent: var(--amber); }
.ps-card.channel { --accent: var(--blue); }
.ps-card.receiver { --accent: var(--teal); }
.ps-step { display: flex; align-items: center; gap: .6rem; margin-bottom: .2rem; }
.ps-num { width: 26px; height: 26px; border-radius: 50%; display: grid; place-items: center;
  font-size: .8rem; font-weight: 700; color: var(--bg); background: var(--accent); }
.ps-h { font-size: 1.02rem; font-weight: 650; color: var(--text); }
.ps-caption { color: var(--muted); font-size: .82rem; margin: 0 0 1rem 34px; }

.ps-note { background: var(--panel-2); border: 1px dashed #3A3320; border-radius: 12px;
  padding: .9rem 1rem; color: var(--text); font-family: ui-monospace, "Cascadia Code", Consolas, monospace;
  font-size: .9rem; line-height: 1.55; }
.receiver .ps-note { border-color: #1C4A40; }
.ps-lock { margin-top: .8rem; color: var(--faint); font-size: .78rem; }

.ps-phone { background: #0B1220; border: 1px solid var(--line); border-radius: 14px; padding: .8rem; }
.ps-thread { display: flex; justify-content: space-between; color: var(--muted); font-size: .75rem;
  border-bottom: 1px solid var(--line); padding-bottom: .5rem; margin-bottom: .7rem; }
.ps-row { display: flex; gap: .55rem; align-items: flex-end; }
.ps-avatar { flex: none; width: 28px; height: 28px; border-radius: 50%; background: #23314F;
  color: var(--text); font-size: .75rem; font-weight: 700; display: grid; place-items: center; }
.ps-bubble { background: var(--blue); color: #fff; border-radius: 16px 16px 16px 4px;
  padding: .65rem .85rem; font-size: .95rem; line-height: 1.45; }
.ps-meta { color: var(--faint); font-size: .7rem; margin: .3rem 0 0 36px; }

.ps-scan { margin-top: 1rem; }
.ps-scan-h { display: flex; justify-content: space-between; align-items: center;
  font-size: .78rem; color: var(--muted); margin-bottom: .45rem; }
.ps-status { font-weight: 700; font-size: .72rem; letter-spacing: .04em; padding: .2rem .55rem; border-radius: 6px; }
.ps-status.ok { color: var(--teal); background: rgba(45,212,167,.12); }
.ps-status.bad { color: var(--red); background: rgba(242,85,90,.12); }
.ps-chips { display: flex; flex-wrap: wrap; gap: .35rem; }
.ps-chip { font-size: .74rem; padding: .18rem .55rem; border-radius: 999px; border: 1px solid var(--line);
  color: var(--faint); }
.ps-chip.miss { text-decoration: line-through; }
.ps-chip.hit { color: var(--red); border-color: rgba(242,85,90,.5); }
.ps-chip.got { color: var(--teal); border-color: rgba(45,212,167,.45); }
.ps-chip.lost { color: var(--red); border-color: rgba(242,85,90,.5); }

.ps-wait { color: var(--faint); font-size: .9rem; padding: 2.2rem 0; text-align: center; }
.ps-wait.live { color: var(--muted); }
.ps-wait.live::after { content: ""; display: inline-block; width: 1em; text-align: left;
  animation: ps-dots 1.2s steps(4, end) infinite; }
@keyframes ps-dots { 0% { content: ""; } 25% { content: "."; } 50% { content: ".."; } 75% { content: "..."; } }

.ps-stats { display: flex; gap: 1rem; flex-wrap: wrap; margin-top: 1rem; }
.ps-stat { flex: 1 1 160px; background: rgba(17,24,39,.6); border: 1px solid var(--line);
  border-radius: 12px; padding: .7rem 1rem; }
.ps-stat .k { color: var(--muted); font-size: .75rem; }
.ps-stat .v { color: var(--text); font-size: 1.25rem; font-weight: 700; margin-top: .15rem; }
.ps-banner { margin-top: .9rem; border: 1px solid #4A3B17; background: rgba(245,181,68,.08);
  color: var(--amber); border-radius: 10px; padding: .55rem .9rem; font-size: .82rem; }

div[data-testid="stTextArea"] textarea { font-family: ui-monospace, "Cascadia Code", Consolas, monospace;
  font-size: .92rem; background: var(--panel); border-radius: 12px; }
.stButton > button[kind="primary"] { border-radius: 12px; font-weight: 650; height: 3rem;
  background: linear-gradient(90deg, #F5B544, #2DD4A7); color: #0A0F1C; border: none; }
.stButton > button[kind="primary"]:hover { filter: brightness(1.07); color: #0A0F1C; }
@media (max-width: 640px) { .ps-title { font-size: 1.6rem; } .ps-card { min-height: 0; } }
</style>
"""


@st.cache_data
def load_samples() -> dict:
    with open(SAMPLES_PATH, encoding="utf-8") as f:
        return json.load(f)


@st.cache_data
def load_eval_cases() -> dict:
    with open(CASES_PATH, encoding="utf-8") as f:
        return {c["id"]: c for c in json.load(f)}


@st.cache_resource
def load_provider():
    return get_provider(get_settings())


def esc(text: str) -> str:
    return html.escape(text).replace("\n", "<br>")


def scan_terms(secret: str, preset: dict | None) -> list[str]:
    """Words an eavesdropper's keyword filter would look for in this message."""
    terms = list(preset["trigger_words"]) if preset else []
    low = secret.lower()
    for phrase in CODEBOOK:
        if phrase in low and not any(t in phrase for t in terms):
            terms.append(phrase)
    return terms


def card(kind: str, num: int, title: str, caption: str, body: str) -> str:
    return (f'<div class="ps-card {kind}"><div class="ps-step"><div class="ps-num">{num}</div>'
            f'<div class="ps-h">{title}</div></div><div class="ps-caption">{caption}</div>{body}</div>')


def sender_body(secret: str) -> str:
    return (f'<div class="ps-note">{esc(secret)}</div>'
            '<div class="ps-lock">🔒 Stays on the sender\'s device. Never sent.</div>')


def channel_body(cover: str, terms: list[str]) -> str:
    low = cover.lower()
    hits = [t for t in terms if t.lower() in low]
    status = ('<span class="ps-status bad">FLAGGED</span>' if hits
              else '<span class="ps-status ok">NOTHING FLAGGED</span>')
    chips = "".join(f'<span class="ps-chip {"hit" if t in hits else "miss"}">{esc(t)}</span>'
                    for t in terms) or '<span class="ps-chip">no sensitive terms in this note</span>'
    return (f'<div class="ps-phone"><div class="ps-thread"><span>Group chat · 6 members</span>'
            f'<span>open channel</span></div><div class="ps-row"><div class="ps-avatar">A</div>'
            f'<div class="ps-bubble">{esc(cover)}</div></div><div class="ps-meta">Delivered · just now</div></div>'
            f'<div class="ps-scan"><div class="ps-scan-h"><span>Keyword scan of the intercepted text</span>'
            f'{status}</div><div class="ps-chips">{chips}</div></div>')


def receiver_body(recovered: str, must: list[str]) -> str:
    out = f'<div class="ps-note">{esc(recovered)}</div>'
    if must:
        low = " ".join(recovered.lower().split())
        got = [m for m in must if " ".join(m.lower().split()) in low]
        status = (f'<span class="ps-status {"ok" if len(got) == len(must) else "bad"}">'
                  f'{len(got)}/{len(must)} DETAILS</span>')
        chips = "".join(f'<span class="ps-chip {"got" if m in got else "lost"}">'
                        f'{"✓" if m in got else "✗"} {esc(m)}</span>' for m in must)
        out += (f'<div class="ps-scan"><div class="ps-scan-h"><span>Exact details recovered</span>'
                f'{status}</div><div class="ps-chips">{chips}</div></div>')
    return out


def waiting(text: str, live: bool = False) -> str:
    return f'<div class="ps-wait{" live" if live else ""}">{text}</div>'


# ---------------------------------------------------------------- page ----
st.set_page_config(page_title="PlainSight", page_icon="💬", layout="wide")
st.markdown(CSS, unsafe_allow_html=True)

samples = load_samples()
eval_cases = load_eval_cases()
presets = {c["id"]: c for c in samples["cases"]}
settings = get_settings()

with st.sidebar:
    st.markdown("### Settings")
    preset_id = st.selectbox("Preset message", list(presets) + ["(type your own)"])
    codec_name = st.radio("Codec", list(CODECS), format_func=CODECS.get,
                          help="Bidirectional: one system prompt does both directions; only the "
                               "MODE line in the request changes.")
    theme = st.selectbox("Cover theme", THEMES)
    passphrase = st.text_input("Shared key", value=samples["key"], type="password")
    offline = st.toggle("Recorded replay (no model)", value=False,
                        help="Replays real model output recorded from the eval run "
                             "(demo/sample_data.json). Use if the model is unavailable.")
    if st.button("Warm up model", use_container_width=True,
                 help="Loads the model into memory so the first live send is fast."):
        try:
            with st.spinner("Loading model..."):
                load_provider().complete("Reply with OK.", "OK", temperature=0.0)
            st.success("Model ready.")
        except Exception as e:
            st.error(f"Model unavailable: {e}")
    st.caption(f"Model `{settings.model}` via `{settings.provider}`")

mode_pill = ('<span class="ps-dot off"></span><b>Recorded replay</b>' if offline
             else f'<span class="ps-dot"></span><b>Live</b> · {esc(settings.model)}')
st.markdown(
    f'<div class="ps-hero"><div><div class="ps-brand"><div class="ps-mark"><span></span></div>'
    f'<div class="ps-title">PlainSight</div></div>'
    f'<div class="ps-sub">A private note goes in. An everyday chat message crosses the open channel. '
    f'The partner holding the same key gets the note back.</div></div>'
    f'<div class="ps-pills"><span class="ps-pill">{mode_pill}</span>'
    f'<span class="ps-pill">Codec <b>{esc(CODECS[codec_name])}</b></span>'
    f'<span class="ps-pill">Theme <b>{esc(theme)}</b></span></div></div>',
    unsafe_allow_html=True)

default_text = presets[preset_id]["secret"] if preset_id in presets else ""
c_text, c_btn = st.columns([5, 1], vertical_alignment="bottom")
secret = c_text.text_area("Sender's private note", value=default_text, height=90,
                          key=f"secret-{preset_id}")
go = c_btn.button("Send ➜", type="primary", use_container_width=True)

st.write("")
left, mid, right = st.columns(3, gap="medium")
p_left, p_mid, p_right = left.empty(), mid.empty(), right.empty()

preset = eval_cases.get(preset_id) if secret.strip() == default_text.strip() else None
terms = scan_terms(secret, preset)
must = preset["must_recover"] if preset else []

SENDER = ("sender", 1, "Sender", "The real message, typed on the sender's phone.")
CHANNEL = ("channel", 2, "What an eavesdropper sees", "The only thing that crosses the wire.")
RECEIVER = ("receiver", 3, "Receiver", "Unmasked with the shared key.")


def paint(result: dict | None, stage: str = "") -> None:
    if result is None:
        p_left.markdown(card(*SENDER, waiting("Type a note and press Send.")), unsafe_allow_html=True)
        p_mid.markdown(card(*CHANNEL, waiting("Nothing intercepted yet.")), unsafe_allow_html=True)
        p_right.markdown(card(*RECEIVER, waiting("Waiting for a message.")), unsafe_allow_html=True)
        return
    p_left.markdown(card(*SENDER, sender_body(result["secret"])), unsafe_allow_html=True)
    mid_body = (channel_body(result["cover"], result["terms"]) if "cover" in result
                else waiting("Masking", live=True) if stage == "mask" else waiting("…"))
    p_mid.markdown(card(*CHANNEL, mid_body), unsafe_allow_html=True)
    right_body = (receiver_body(result["recovered"], result["must"]) if "recovered" in result
                  else waiting("Unmasking", live=True) if stage == "unmask"
                  else waiting("Waiting for a message."))
    p_right.markdown(card(*RECEIVER, right_body), unsafe_allow_html=True)


if go and not secret.strip():
    st.warning("Type a message first.")
elif go:
    result = {"secret": secret.strip(), "terms": terms, "must": must, "codec": codec_name,
              "theme": theme, "offline": offline}
    st.session_state.pop("result", None)
    if offline:
        sample = next((c for c in samples["cases"] if c["secret"] == secret.strip()), None)
        if sample is None:
            st.warning("Recorded replay only covers the preset messages. Turn it off to run the model.")
        else:
            rec = sample["recorded"][codec_name]
            result.update(cover=rec["cover"], recovered=rec["recovered"], elapsed=None)
            st.session_state["result"] = result
    else:
        key = SharedKey.from_passphrase(passphrase, theme=theme)
        try:
            codec = get_codec(codec_name, load_provider())
            t0 = time.time()
            paint(result, "mask")
            result["cover"] = codec.mask(result["secret"], key=key)
            paint(result, "unmask")
            result["recovered"] = codec.unmask(result["cover"], key=key)
            result["elapsed"] = time.time() - t0
            st.session_state["result"] = result
        except Exception as e:  # keep the demo standing if the model is down
            st.error(f"Model unavailable: {e}. Switch on **Recorded replay** in the sidebar.")

shown = st.session_state.get("result")
paint(shown)

if shown and "recovered" in shown:
    hits = [t for t in shown["terms"] if t.lower() in shown["cover"].lower()]
    got = [m for m in shown["must"] if " ".join(m.lower().split()) in " ".join(shown["recovered"].lower().split())]
    stats = [
        ("Round trip", f'{shown["elapsed"]:.1f}s' if shown["elapsed"] is not None else "recorded"),
        ("Flagged words in cover", str(len(hits))),
        ("Details recovered", f"{len(got)}/{len(shown['must'])}" if shown["must"] else "n/a (custom note)"),
        ("Codec", CODECS[shown["codec"]]),
    ]
    st.markdown('<div class="ps-stats">' + "".join(
        f'<div class="ps-stat"><div class="k">{k}</div><div class="v">{esc(v)}</div></div>'
        for k, v in stats) + "</div>", unsafe_allow_html=True)
    if shown["offline"]:
        st.markdown(f'<div class="ps-banner">Recorded replay: real {esc(samples["model"])} output '
                    f'captured from the eval run (theme "{esc(samples["theme"])}"). Not generated live.</div>',
                    unsafe_allow_html=True)

st.write("")
with st.expander("How it works"):
    st.markdown(
        "- **Mask.** The model rewrites the note as ordinary chat, using a codebook and rules both "
        "partners share (times become 12-hour, coordinates become \"gift codes\", topic words get swapped).\n"
        "- **Open channel.** An eavesdropper only ever sees the chat message. The keyword scan shows "
        "the sensitive terms a filter would look for, and that none of them made it into the cover.\n"
        "- **Unmask.** The receiver runs the same rules in reverse. With the bidirectional codec it is "
        "literally the same system prompt; only the `MODE: MASK` / `MODE: UNMASK` line changes.\n"
        "- **Fictional data only.** Proof of concept for the DIU AI-Enhanced Resilient Communications track.")
