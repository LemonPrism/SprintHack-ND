# demo/ — Stage 3 UI

Three panes: **sender's private note / what an eavesdropper sees / receiver's
recovered note**, plus an optional **face key** that locks the shared key to
your face. The app only calls the `Codec` interface and `plainsight.biometric`;
it does not reimplement masking.

## Run it
```bash
# Ollama app running, model pulled: ollama pull qwen2.5:7b
.venv\Scripts\activate          # Windows (macOS/Linux: source .venv/bin/activate)
pip install -r requirements.txt
streamlit run demo/app.py       # from the repo root; opens http://localhost:8501
```
Run it from the repo root so `.streamlit/config.toml` (the dark theme) loads. The face
models (~39 MB) download into `models/` on first use.

## Walkthrough

**Screen layout.** Left sidebar: *Settings* on top, *Face key* below. Main area: the header
(status pills), the note box with **Send ➜**, the three panes, a stats row, and the
expanders at the bottom.

### 1. Set up (sidebar → Settings)
1. **Warm up model**: click it once and wait for "Model ready." (the first load is slow on CPU).
2. **Preset message**: pick `book-swap` (or `(type your own)` to write a note).
3. **Codec**: *One bidirectional prompt* (default) or *Two prompts* (the baseline).
4. **Cover theme**: the kind of chat the message is disguised as.
5. **Shared key**: the passphrase both partners hold (`sprinthack-demo` by default).
6. **Recorded replay**: leave it **off** for a live run. Turn it on only if the model is down;
   it replays real recorded output for the preset messages and says so on screen.

### 2. Lock the key to your face (sidebar → Face key), optional
1. *First time:* check the **Shared key** field, optionally type a **Face PIN**, then click
   **Enroll face**. A live camera view opens in the main area: the box and five tracked
   points (eyes, nose, mouth corners) turn teal on usable frames. Hold still, facing the
   camera, until the bar reaches 20/20. You'll see "Face enrolled", and the vault is unlocked.
2. *Every later session:* type the same PIN (if you set one), click **Unlock**, look at the
   camera until 12/12. "Face recognized. Vault unlocked."
3. While unlocked, the header shows **Key 🔓 face vault**, the shared key comes from the
   vault (not the text field), and an **Encrypt or decrypt with your face key** expander
   appears at the bottom.
4. **Lock** forgets the unlocked key for this session. To start over, delete
   `.plainsight/face_vault.json` (or `python -m plainsight.face_cli forget`).

### 3. Send a message (main area)
1. Check the text in **Sender's private note**, then click **Send ➜**.
2. Pane **1 · Sender** shows the real note ("Stays on the sender's device").
3. Pane **2 · What an eavesdropper sees** fills in first (≈10 s): the disguised chat bubble,
   then the **keyword scan** — the sensitive words a filter would look for, struck through,
   and **NOTHING FLAGGED** if none made it into the cover.
4. Pane **3 · Receiver** fills in next: the recovered note and the **exact details** check
   (for presets, e.g. **6/6 DETAILS** with each coordinate / time / name / day ticked).
5. The **stats row** below shows the round-trip time, flagged words, details recovered and codec.

### 4. Encrypt / decrypt with your face key (when unlocked)
1. Open **Encrypt or decrypt with your face key** at the bottom.
2. Left: type text → **Encrypt** → copy the `psf1:…` token.
3. Right: paste a token → **Decrypt** → the original text. Tokens only open with your face key.

### 5. Learn more
**How it works** (bottom expander) summarizes mask → open channel → unmask and the face key.

## Before you present
1. Click **Warm up model**. Use the **book-swap** preset; it is the case the prompts are
   tuned for. Expect ~10-20 s per live round trip on a laptop CPU once warm.
2. If you'll show the face key, enroll before the talk (in the same lighting), then
   **Lock**, so on stage you only click **Unlock**.
3. If the model misbehaves, switch on **Recorded replay**.
4. Fallback recording of a real live run (book-swap, 17.2 s round trip): `demo/demo-fallback.gif`
   (recorded before the restyle, so it shows the old look).
5. Face check from the terminal: `python -m plainsight.face_cli selftest`.
