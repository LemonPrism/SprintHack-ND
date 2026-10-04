# demo/ — Stage 3 UI

The three-pane demo: **sender's real message → what the open channel (the adversary)
sees → receiver's recovered message**. Making the adversary's view visible IS the pitch.

## Run it

```bash
# one-time: pip install -r requirements.txt  (includes streamlit)
#           ollama pull qwen2.5:7b           (the local, free model)
streamlit run demo/app.py
```

It opens in your browser. The provider/model come from `.env` (local Ollama by
default), so no API key is needed. The first "Send" is slow while Ollama loads the
model; later runs are fast.

## Narrate the three panes

1. **Pick a codec** (sidebar): *Stage 1 · prompt-only* reads perfectly benign;
   *Stage 2 · keyed* adds lossless, key-dependent recovery.
2. **Load an example secret** (sidebar) or type your own, then **Send through PlainSight →**.
3. Read left to right:
   - **① Sender sees** — the real clandestine message.
   - **② Open channel sees** — the only thing the adversary intercepts. Point out
     there are no operational words; it looks like ordinary chatter.
   - **③ Receiver recovers** — the message back out. "✅ Exact match" when it's
     byte-for-byte.
4. **The key moment:** change the *Receiver key* in the sidebar and re-send with the
   keyed codec. Recovery fails — proof that holding the model is not enough; you need
   the key. That's the "safe to be caught with" story.

## Design note

The UI is thin on purpose: it only calls `get_codec(...)`, `mask`, and `unmask`
through the `Codec` interface. It never reimplements masking, so a new codec or
provider appears here for free.

Record a 60–90s screen capture of the above as a live-demo fallback.
