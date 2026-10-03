# demo/ — Stage 3 UI

The three-pane demo lives here: **sender's real message / intercepted channel view
(what the adversary sees) / receiver's recovered message**.

Two easy paths:
- **Streamlit** (`pip install streamlit`, add to requirements), three columns calling
  `plainsight.codecs.get_codec("prompt", provider)`.
- **Published HTML artifact** that calls the model API directly (no backend).

Keep the UI thin: it should only call the `Codec` interface, never reimplement masking.
Record a 60–90s capture as a live-demo fallback.
