# TASKS.md — PlainSight build plan

Work top to bottom. **Check the acceptance command before ticking a box.**
`[ ]` = todo, `[~]` = in progress, `[x]` = done & verified.

Legend for effort: ⬤ small (<1h) · ⬤⬤ medium (1–3h) · ⬤⬤⬤ large (3h+)

---

## Stage 0 — Setup & alignment ⬤
Goal: everyone can run the skeleton and the harness.

- [x] Create `.venv`, `pip install -r requirements.txt`
- [x] `cp .env.example .env` (defaults to local Ollama `qwen2.5:7b` — no API key needed)
- [ ] Read `CLAUDE.md` threat model + MVP definition out loud as a team
- [ ] Pick the demo scenario (default: `shahed-factory` in `evaluation/cases.json`)

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
`plainsight/prompts/lexicon.py` (shared cover lexicon), `plainsight/codecs/prompt_codec.py`.

- [x] Flesh out the encode system prompt (benign, no trigger words, preserve recoverable detail, output only the message)
- [x] Flesh out the decode system prompt (recover original, output only the message)
- [x] Make `mask` / `unmask` work via the CLI on the `shahed-factory` secret
- [x] Iterate prompts until the frozen cases pass the threshold (100% on `qwen2.5:7b`)
- [~] (easy win) Add a `--theme` cover-domain selector end to end — wired through, but the 7B model
  barely varies the cover by theme (lexicon/examples are party-flavoured); needs per-theme examples
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

- [x] Extend `fields.extract_fields` to catch coords / times / dates / names / places in the cases
- [x] Implement `KeyedFieldCodec.mask`: pack secret+fields → key-disguise → embed in benign LLM cover
- [x] Implement `KeyedFieldCodec.unmask`: pull payload → undisguise → rebuild the exact secret (lossless)
- [x] Make the payload disguise key-dependent (SHA-256 keystream from `key.passphrase`; wrong key → garbage)

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

- [x] Minimal web UI (Streamlit, `demo/app.py`) with the three panes
- [x] Theme/persona dropdown wired to the cover theme
- [x] A "what the open channel sees" panel showing only the benign cover (plus a live wrong-key demo)
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

- [x] **On-device local models** — `OllamaProvider(LLMProvider)` added (PoC default; free, no API key)
- [ ] **Bidirectional single model** polish (already partly in Stage 1)
- [ ] **Multilingual** — add a `language` param threaded through prompts/`SharedKey`
- [ ] **Pattern / determinism mitigation** — key-seeded RNG so same input ≠ same cover
- [ ] **Objective benign-ness scoring** — a real `BenignScorer` (perplexity / classifier) replacing the trigger-word proxy
- [ ] **Traffic blending** — a layer that conditions cover on a sample of real channel traffic (the metadata angle)
- [ ] **Image / photo carriers** — a `Codec` whose cover is an image caption or an image
- [ ] **Key separation / seized-model safety** — model alone cannot decode without the key
- [ ] **Per-user model diversity** — distinct small models so one seizure ≠ global compromise
- [ ] **Robust adversarial testing** — active-warden paraphrase/normalization survival
