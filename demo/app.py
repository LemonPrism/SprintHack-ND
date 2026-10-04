"""Stage 3 — three-pane live demo.

    streamlit run demo/app.py

Sender's real message | what an eavesdropper sees | receiver's recovered message.
Thin UI: it only calls the Codec interface (plus a labelled offline replay of
demo/sample_data.json in case the model is unavailable during a pitch).
"""
from __future__ import annotations
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

SAMPLES_PATH = os.path.join(ROOT, "demo", "sample_data.json")
THEMES = ["party and gift planning", "weekend sports chat", "family group text", "dinner plans"]


@st.cache_data
def load_samples() -> dict:
    with open(SAMPLES_PATH, encoding="utf-8") as f:
        return json.load(f)


@st.cache_resource
def load_codec():
    return get_codec("prompt", get_provider(get_settings()))


st.set_page_config(page_title="PlainSight demo", page_icon="💬", layout="wide")
st.title("PlainSight")
st.caption("A private note goes in, an everyday chat message goes over the open channel, "
           "and the partner holding the same key gets the note back.")

samples = load_samples()
presets = {c["id"]: c for c in samples["cases"]}

with st.sidebar:
    st.header("Settings")
    preset_id = st.selectbox("Preset message", list(presets) + ["(type your own)"])
    theme = st.selectbox("Cover theme", THEMES)
    passphrase = st.text_input("Shared key", value=samples["key"], type="password")
    offline = st.toggle("Offline replay (no model)", value=False,
                        help="Replays the hand-written sample covers in demo/sample_data.json. "
                             "Use only if the model is unavailable.")
    if st.button("Warm up model", help="Loads the model into memory so the first live send is fast."):
        try:
            with st.spinner("Loading model..."):
                load_codec()  # build the provider
                get_provider(get_settings()).complete("Reply with OK.", "OK", temperature=0.0)
            st.success("Model ready.")
        except Exception as e:
            st.error(f"Model unavailable: {e}")
    s = get_settings()
    st.caption(f"Model: `{s.model}` via `{s.provider}`")

default_text = presets[preset_id]["secret"] if preset_id in presets else ""
secret = st.text_area("Sender's private note", value=default_text, height=90,
                      key=f"secret-{preset_id}")
go = st.button("Send", type="primary", use_container_width=True)

left, mid, right = st.columns(3)
left.subheader("1 · Sender")
mid.subheader("2 · What an eavesdropper sees")
right.subheader("3 · Receiver")

if go and secret.strip():
    key = SharedKey.from_passphrase(passphrase, theme=theme)
    left.info(secret)

    if offline:
        sample = next((c for c in samples["cases"] if c["secret"] == secret.strip()), None)
        if sample is None:
            mid.warning("Offline replay only has the preset messages. Turn offline off to run the model.")
        else:
            mid.success(sample["cover"])
            right.info(sample["recovered"])
            st.caption("⚠️ Offline replay: hand-written sample, not live model output.")
    else:
        try:
            codec = load_codec()
            t0 = time.time()
            with mid:
                with st.spinner("Masking..."):
                    cover = codec.mask(secret, key=key)
            mid.success(cover)
            with right:
                with st.spinner("Unmasking..."):
                    recovered = codec.unmask(cover, key=key)
            right.info(recovered)
            st.caption(f"Live round trip in {time.time() - t0:.1f}s · theme: {theme}")
        except Exception as e:  # keep the demo standing if the model is down
            mid.error(f"Model unavailable: {e}")
            st.caption("Tip: switch on **Offline replay** in the sidebar.")
elif go:
    st.warning("Type a message first.")
