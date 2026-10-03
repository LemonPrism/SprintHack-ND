# TASKS.md — PlainSight build plan

Work top to bottom. **Check the acceptance command before ticking a box.**
`[ ]` = todo, `[~]` = in progress, `[x]` = done & verified.

Legend for effort: ⬤ small (<1h) · ⬤⬤ medium (1–3h) · ⬤⬤⬤ large (3h+)

---

## Stage 0 — Setup & alignment ⬤
Goal: everyone can run the skeleton and the harness.

- [x] Create `.venv`, `pip install -r requirements.txt`
- [x] `cp .env.example .env` — no API key, so we use a local model: install Ollama, `ollama pull qwen2.5:7b`
- [ ] Read `CLAUDE.md` threat model + MVP definition out loud as a team
- [x] Pick the demo scenario (default: `book-swap` in `evaluation/cases.json`)

**Acceptance check**
```bash
pytest -q                                   # all green
python -m evaluation.run_eval --codec mock  # aggregate recovery = 1.00
```
If the mock run is 1.00, the pipeline and scoring work and you can trust later numbers.

---

## Stage 1 — Core round-trip MVP ⬤⬤  (THIS IS THE GRADED MVP)
Goal: a real LLM masks a secret into benign text and unmasks it back, usably.
Files: `plainsight/prompts/encode.py`, `plainsight/prompts/decode.py`,
`plainsight/codecs/prompt_codec.py`.

- [x] Flesh out the encode system prompt (benign, no trigger words, preserve recoverable detail, output only the message)
- [x] Flesh out the decode system prompt (recover original, output only the message)
- [x] Make `mask` / `unmask` work via the CLI on the `book-swap` secret
- [x] Iterate prompts until the frozen cases pass the threshold
  - Result (qwen2.5:7b via Ollama): frozen cases 100% recovery, all benign, deterministic across runs.
    Uses a shared codebook (`plainsight/prompts/codebook.py`) + few-shot examples.
  - Honest caveat: on 3 unseen messages recovery fell to 78% and no cover passed the benign
    check — topic words missing from the codebook leak through, and the model sometimes
    rounds times (1705 -> 5pm) or mangles numbered places. Stage 2 targets exactly this.
- [x] (easy win) Add a `--theme` cover-domain selector end to end (CLI + eval `--theme`, threaded into both prompts)
- [ ] (easy win) Bidirectional single prompt: one system prompt, `mode=mask|unmask` — judge called this the "fancy" version

**Acceptance check**
```bash
python -m evaluation.run_eval --codec prompt --min-recovery 0.90
# exits 0 when aggregate field-recovery >= 0.90 AND every cover passes the benign check
```
When this passes you have met the judge's stated MVP. Everything below is upside.

---

## Stage 2 — Fidelity layer (our differentiator) ⬤⬤⬤
Goal: exact data (coords, names, times, dates) survives the round-trip losslessly,
instead of trusting the LLM to "remember" it through a paraphrase. This is the
exact failure the judge predicted ("it gets awkward very quick") — beating it is
the pitch.
Files: `plainsight/codecs/fields.py` (core exists), `plainsight/codecs/keyed_field_codec.py` (TODO).

- [ ] Extend `fields.extract_fields` to reliably catch coords / times / dates / names in the cases
- [ ] Implement `KeyedFieldCodec.mask`: extract fields → `pack_fields` → prompt LLM to weave the packed payload into benign `theme` cover
- [ ] Implement `KeyedFieldCodec.unmask`: pull the payload back out → `unpack_fields` → rebuild the exact secret
- [ ] Make the payload disguise key-dependent (use `SharedKey` to seed how fields are hidden)

**Acceptance check**
```bash
python -m evaluation.run_eval --codec keyed --min-recovery 0.98
# keyed codec should beat prompt-only on exact-field recovery (aim 0.98+)
```
Show the before/after: `prompt` recovery vs `keyed` recovery on the same cases.

---

## Stage 3 — Demo UI ⬤⬤
Goal: three panes — **sender's real message / intercepted channel view / receiver's recovered message**.
Making the adversary's view visible IS the pitch. Lives in `demo/`.

- [x] Minimal web UI (Streamlit, or a published HTML artifact calling the API) with the three panes — `demo/app.py`
- [x] Theme/persona dropdown wired to `--theme`
- [x] A "what an eavesdropper sees" panel that shows only the benign text
- [ ] Record a 60–90s screen capture as a live-demo fallback

**Acceptance check**: a teammate who has never seen it can run the demo and narrate the three panes unaided.

---

## Stage 4 — Evaluation polish ⬤
Goal: honest numbers for the deck.

- [ ] Add a results table export (per-case recovery + benign_ok) to `evaluation/`
- [ ] Add a crude benign-ness proxy beyond trigger words (optional: perplexity or an LLM-judge pass)
- [ ] Capture the `prompt` vs `keyed` comparison chart for slide 7/8

**Acceptance check**: `python -m evaluation.run_eval --codec keyed --report out.json` writes a readable report.

---

## Stage 5 — Deck & rehearse ⬤⬤
- [ ] Slides per the structure in the project notes (problem → why today fails → idea → how → demo → the hard part we solved → benign check → feasibility → limits → roadmap → vision)
- [ ] Open with the Afghan evacuation / Green Revolution framing (the judge's own stories)
- [ ] Rehearse with the recorded fallback ready

---

## Long-term backlog (NOT for the hackathon — list these as "future improvements")
Each maps to an extension point in `ARCHITECTURE.md`. Build order is rough.

- [x] **On-device local models** — `OllamaProvider(LLMProvider)` added (now our dev provider; no API key)
- [ ] **Bidirectional single model** polish (already partly in Stage 1)
- [ ] **Multilingual** — add a `language` param threaded through prompts/`SharedKey`
- [ ] **Pattern / determinism mitigation** — key-seeded RNG so same input ≠ same cover
- [ ] **Objective benign-ness scoring** — a real `BenignScorer` (perplexity / classifier) replacing the trigger-word proxy
- [ ] **Traffic blending** — a layer that conditions cover on a sample of real channel traffic (the metadata angle)
- [ ] **Image / photo carriers** — a `Codec` whose cover is an image caption or an image
- [ ] **Key separation / seized-model safety** — model alone cannot decode without the key
- [ ] **Per-user model diversity** — distinct small models so one seizure ≠ global compromise
- [ ] **Robust adversarial testing** — active-warden paraphrase/normalization survival
