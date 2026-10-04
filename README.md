# PlainSight

Masking & unmasking of plaintext with generative AI — a codebook replacement.
DIU "AI-Enhanced Resilient Communications" track, SprintHack@ND 2026.

**New here (human or Claude)? Read this README's status section first, then
`CLAUDE.md`, `TASKS.md`, and `ARCHITECTURE.md`.**

---

## Current status (handoff, 2026-10-03, second round)

| Stage | Status | Where |
|---|---|---|
| 0 — Setup | ✅ done | `.venv`, `.env` (git-ignored), Ollama |
| 1 — Core round-trip MVP (graded) | ✅ passing, incl. bidirectional single prompt | `plainsight/prompts/`, `plainsight/codecs/prompt_codec.py`, `bidi_prompt_codec.py` |
| 2 — Fidelity layer (`KeyedFieldCodec`) | ❌ not started (scaffold only) | `plainsight/codecs/keyed_field_codec.py` |
| 3 — Demo UI | ✅ done and restyled; fallback GIF shows the old look | `demo/app.py`, `.streamlit/config.toml` |
| 4 — Evaluation polish | 🟡 results-table export done; extra benign proxy and prompt-vs-keyed chart not done | `evaluation/export_table.py`, `evaluation/results.md` |
| 5 — Deck & rehearse | 🟡 deck drafted (12 slides, speaker notes); rehearsal not done | `deck/PlainSight.pptx` |

**Latest numbers** (`qwen2.5:7b` on a laptop CPU via Ollama, temperature 0):
- `python -m evaluation.run_eval --codec prompt` → **100% field recovery, 3/3 covers benign, PASS**
  (identical output across runs). Full table: `evaluation/results.md` / `.csv`.
- Caveat: on 3 unseen messages, recovery fell to **78%** and no cover passed the benign check
  — topic words missing from the codebook leak into the cover, and the model sometimes rounds
  times (1705 → 5pm). The book-swap decode also invents a place ("road work") that the scorer
  doesn't check. Details in `TASKS.md` (Stage 1).
- `--codec bidi` (one system prompt, `MODE:` line) → **100%, 3/3 benign, PASS**, deterministic.
  On 3 new unseen messages: bidi 92% / 3 of 3 benign vs two-prompt 92% / 2 of 3 benign. Both still invent or
  drop places/topics (e.g. "Route 12" copied from a prompt example) and both got 1705 wrong.
- Live demo round trip: ~17s warm, ~66s cold.

**Face key (new, optional)** — your face unlocks a local encrypted vault that holds the shared key, and can
encrypt/decrypt text. See "Face key" below. Verified on unit tests, on a real face photo (detection,
landmarks, enroll/unlock, wrong PIN) and in the demo app headless. **Live webcam selftest passed
(2026-10-03):** enroll 20/20 frames; 3/3 unlocks (similarity 0.96 / 0.94 / 0.84); wrong PIN and an impostor
photo (similarity 0.05) rejected. One session, one lighting setup; other conditions not yet measured.

**Not done:**
- **Stage 2** (`KeyedFieldCodec`) — scaffold only.
- Deck: rehearse it, and swap in a fresh demo screenshot/GIF of the restyled UI if wanted.
- The deck generator (pptxgenjs) is not in the repo; edit `deck/PlainSight.pptx` directly in PowerPoint.

### What changed in the second round
- **Bidirectional codec** — `plainsight/prompts/bidirectional.py` + `codecs/bidi_prompt_codec.py`, registered as
  `bidi` in the factory, CLI and eval. Unit test in `tests/test_prompt_codec.py`.
- **Demo restyle** — dark theme, three cards (note / chat bubble / recovered note), keyword-scan chips on the
  intercept, exact-detail chips on the receiver, codec switch, stats row. `sample_data.json` now holds **real
  recorded model output** for both codecs (it used to be hand-written placeholders).
- **Deck** — `deck/PlainSight.pptx`, built from the repo images (Ohio graphic and SVG seal left out).

### What changed in the first round (summary of commits since `448cc44`)
- **Local model, no API key** — `plainsight/providers/ollama_provider.py` (stdlib HTTP, no new
  deps), registered in `providers/__init__.py`; `OLLAMA_HOST_URL` setting in `config.py`;
  `.env.example` defaults to `PLAINSIGHT_PROVIDER=ollama`, `PLAINSIGHT_MODEL=qwen2.5:7b`.
  Requests send `keep_alive=30m` so the model stays loaded.
- **Eval cases replaced with harmless fictional secrets** — `book-swap` (regression anchor),
  `study-group`, `road-work`. They still carry exact coordinates, times, days and names.
  Tests and docs updated to match.
- **Stage 1 prompts** — shared word-swap codebook (`plainsight/prompts/codebook.py`), mirrored
  encode/decode rules for times (0900 ↔ 9am) and coordinates (41.7056 N ↔ gift code 41-7056N),
  and three few-shot examples.
- **`PromptCodec`** now uses the provider's configured temperature (`PLAINSIGHT_TEMPERATURE`,
  default 0.0) instead of hard-coding it.
- **Demo** — `demo/app.py` (Streamlit): sender / eavesdropper / receiver panes, theme dropdown,
  presets, warm-up button, labelled offline replay of `demo/sample_data.json`
  (hand-written placeholders, **not** model output). Fallback GIF of a real live run in
  `demo/demo-fallback.gif`.
- **Results export** — `evaluation/export_table.py` turns a `--report` JSON into Markdown/CSV.
- **Assets** — uploaded images moved to `assets/` with descriptive names (DIU seal/logo/sign,
  DIU locations map, Pentagon aerial, US chip graphic, and an Ohio "Innovation Hubs" graphic —
  that last one is about Ohio's $125M state investment, not DIU or this project).
- **Docs** — `ARCHITECTURE.md` Codec signature fixed (`mask(secret, *, key)`; theme lives in
  `key.theme`); `CLAUDE.md`, `TASKS.md`, `demo/README.md` updated.

### Known loose ends
- `fields.extract_fields` treats "Host Maria Lopez" as a name ("Host" isn't a stop word), and its
  clock regex would read a year like "2026" as a time. Relevant if Stage 2 is picked up.
- `tests/test_roundtrip_live.py` only runs with an Anthropic key; there is no live Ollama test
  in `pytest` (the eval harness covers it).

---

## Quickstart
```bash
python -m venv .venv && source .venv/bin/activate   # Windows: .venv/Scripts/activate
pip install -r requirements.txt
cp .env.example .env     # defaults to local Ollama: install it, then `ollama pull qwen2.5:7b`
                         # (or switch to anthropic and add ANTHROPIC_API_KEY)

python -m plainsight.cli mask "The book swap is at 41.7056 N, 86.2353 W. Open 0900-1200. Host is Maria Lopez. Bring two paperbacks Saturday." --theme "party and gift planning"
python -m plainsight.cli unmask "<benign message>" --theme "party and gift planning"
```
Ollama on Windows: `winget install Ollama.Ollama`, then `ollama pull qwen2.5:7b`.
`llama3.2` (3B) was tried and is too weak (refuses / copies examples; 8% recovery).

## Verify
```bash
pytest -q                                        # 13 passed, 1 skipped (live Anthropic test)
python -m evaluation.run_eval --codec mock       # must be 100% (harness self-test)
python -m evaluation.run_eval --codec prompt     # real masking (Ollama running, or an Anthropic key)
python -m evaluation.run_eval --codec bidi       # same, with the single bidirectional prompt
python -m evaluation.run_eval --codec prompt --report out.json
python -m evaluation.export_table out.json --md evaluation/results.md --csv evaluation/results.csv
```

## Face key
The shared key has to be identical for both partners, so a face cannot *be* that key. Instead your face
unlocks a local vault (`.plainsight/face_vault.json`, git-ignored) that holds it, so a seized device gives
up nothing without your face (and optional PIN).
- **Vision:** OpenCV YuNet tracks the face and 5 landmarks; SFace turns the aligned face into a 128-d
  embedding. Models download once into `models/` (git-ignored) and are SHA-256 pinned.
- **Key:** a fuzzy commitment (`plainsight/biometric/fuzzy.py`) turns the noisy embedding into an exact
  128-bit secret; scrypt(secret + PIN) → AES-256-GCM. No face image, embedding or template is stored.
  Tuned in simulation: similarity ≥ 0.7 unlocks ~97%, ≤ 0.4 unlocks ~0%.
- **Limits:** no liveness check (a good photo of you could unlock it); under coercion a face is easy to
  compel, so set a PIN; repetition-code helper data leaks some bits; first-try unlock rate under different
  lighting is not yet measured.
```bash
python -m plainsight.face_cli selftest [--impostor someone_else.jpg]   # live end-to-end check, throwaway vault
python -m plainsight.face_cli track                                    # live landmark tracking, q to quit
python -m plainsight.face_cli enroll --shared-key sprinthack-demo [--pin 1234]
python -m plainsight.face_cli unlock --show | encrypt "text" | decrypt psf1:...
python -m plainsight.cli mask "secret" --face --codec bidi              # shared key from the vault
```
In the demo app: sidebar → **Face key** → Enroll face / Unlock (live tracking view), then an
encrypt/decrypt panel appears.

## Live demo
```bash
streamlit run demo/app.py      # http://localhost:8501
```
Three panes: sender / what an eavesdropper sees / receiver. Before presenting: click
**Warm up model**, use the **book-swap** preset, and keep **Offline replay** as a backup.
See `demo/README.md` for the full checklist.

## Repo layout (top level)
```
plainsight/   the package (providers, codecs, prompts, key, config, cli, biometric/ face key, face_cli)
evaluation/   frozen cases, scorer, run_eval, export_table, latest results
tests/        pytest (no network needed)
demo/         Streamlit app, sample data, fallback GIF
assets/       images for the deck
deck/         PlainSight.pptx
```

Fictional test data only. Defensive / anti-censorship PoC.
