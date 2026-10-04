# demo/ — Stage 3 UI

Three panes: **sender's private note / what an eavesdropper sees / receiver's
recovered note**. The app only calls the `Codec` interface; it does not
reimplement masking.

## Run it
```bash
# Ollama app running, model pulled: ollama pull qwen2.5:7b
.venv\Scripts\activate          # Windows (macOS/Linux: source .venv/bin/activate)
pip install -r requirements.txt
streamlit run demo/app.py       # opens http://localhost:8501
```

## Before you present
1. Open the app and click **Warm up model** in the sidebar (first load is slow on CPU).
2. Use the **book-swap** preset; it is the case the prompts are tuned for.
   Expect ~10-20s per live round trip on a laptop CPU once warm.
3. If the model misbehaves, switch on **Offline replay**. It replays the
   hand-written covers in `sample_data.json` and labels them as such on screen.
4. Fallback recording of a real live run (book-swap, 17.2s round trip): `demo/demo-fallback.gif`.
