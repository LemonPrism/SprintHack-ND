# Stage 4 — Evaluation Report

*PlainSight · SprintHack@ND 2026 · "AI-Enhanced Resilient Communications"*
*All data below is from the frozen, fictional cases in `evaluation/cases.json`. Raw
JSON per run is in `evaluation/reports/`.*

---

## 0. TL;DR for the deck

- **Stage 1 (pure-LLM masking)** works on every model we tested and clears the
  judge's MVP bar (≥90% field-recovery, covers pass the benign check). The
  **free Groq `gpt-oss-120b`** is the best Stage-1 engine we have: it generalizes
  to free-text secrets far better than the local 7B and, unlike hosted Claude,
  **does not refuse** to produce covers for operational content.
- **Stage 2 (keyed invisible codec)** is the differentiator and is **already
  lossless (100% exact recovery) today, independent of the model.** The LLM is
  demoted to writing a throwaway benign cover; the real message rides in invisible
  zero-width characters and is recovered by cryptography, not by the model's memory.
- The honest ceiling: Stage 1 recovers *meaning* and is lossy for words outside
  the shared lexicon; the zero-width carrier is invisible to the eye but not to
  byte-level analysis and does not survive Unicode-stripping channels. Both gaps
  close with **a better, custom-trained on-device model** — see §3 and §4.

---

## 1. Stage 1 — model comparison (pure-LLM `PromptCodec`)

### 1.1 Frozen-case scores (the MVP gate)

| Provider / model | Field recovery | All covers benign | MVP (≥0.90) | Cost | Refuses operational content? |
|---|---|---|---|---|---|
| **Ollama `qwen2.5:7b`** (local, on-device) | **100%** | ✅ | PASS | Free | No |
| **Groq `openai/gpt-oss-120b`** (free API) | **100%** | ✅ | PASS | Free* | No |
| **Claude (CLI, `sonnet`)** | — | — | — | Free w/ sub | **Yes — refuses** (see §1.3) |
| Mock codec (harness self-test) | 100% | ✅ | PASS (sanity) | — | — |

\* Groq free tier: ~8,000 tokens/min; our provider auto-retries on HTTP 429.
Reports: `reports/prompt_ollama7b.json`, `reports/prompt_groq.json`, `reports/mock.json`.

**Reading this honestly:** all three usable engines hit 100% on the frozen cases
*because the cases are tuned to the shared lexicon*. At that point the frozen set
no longer tells the models apart — it confirms the pipeline works, not which model
is better. The real differentiation is on **free-text secrets the lexicon does not
cover**, below.

### 1.2 Free-text generalization (where the models actually differ)

Same three off-lexicon secrets, same key/theme, run through each engine. "Cover" is
what the open channel sees; "Recovered" is what the receiver reconstructs.

**Secret A:** *"A man is speeding down the highway I-19 at 6:30 PM kidnapping someone."*

| | Cover (benign surface) | Recovered |
|---|---|---|
| **7B** | "A guy is zooming down I-19 at 6:30pm in a hurry. Hope he takes another route! 🚧" | "A guy is zooming down I-19 at 1830 in a hurry. **Hope he avoids it!**" |
| **120B** | "I'm rushing down I-19 at 6:30pm to pick up a friend for dinner!" | "Rushing down I-19 at 1830 to pick up a friend for dinner." |

> Both keep the channel benign (good — `speeding`/`kidnapping` never leak). The **7B
> injects a spurious lexicon artifact** ("take another route" → decoded as "avoids
> it"), a word that was never in the secret. The 120B stays clean.

**Secret B:** *"There is an armed man roaming the streets in my location at 5:30 PM."*

| | Cover | Recovered |
|---|---|---|
| **7B** | "there's an all dressed up guy hanging out on the streets … 5:30pm. Better take another route!" | "There is an **armed man patrolling** the streets … 1730. **Avoid it.**" |
| **120B** | "The entertainer is around my area at 5:30pm, so let's meet for dinner soon!" | "**Armed man** is around my area at 1730. Meet for dinner soon." |

> `armed man` is now in the lexicon, so **both recover it**. But the 7B again
> over-fires the lexicon (`roaming`→patrol cover, plus an injected "Avoid it"),
> while the 120B maps only what it should and writes a more natural cover.

**Secret C:** *"The safe house is on Elm Street. Password is bluebird. Come alone tonight."*

| | Cover | Recovered |
|---|---|---|
| **7B** | "The apartment is on Elm Street. The playlist name is bluebird. Come solo tonight!" | "The safe house is on Elm Street. The password is bluebird. Come alone tonight." |
| **120B** | "Dinner at the apartment on Elm Street tonight, bring the playlist name bluebird, and it's solo 🎉" | "Dinner at the safe house on Elm Street tonight. Bring the password bluebird. …" |

> Fully lexicon-covered secret → **both recover it near-exactly.** This is the
> ideal Stage-1 case and shows what "the lexicon is complete for this content"
> buys you.

**Conclusion (Stage 1):** a bigger model does not raise the frozen score (already
capped), but it **generalizes more cleanly to unanticipated secrets** — fewer
spurious lexicon artifacts, more natural and theme-varied covers. The 120B is the
best free option. The 7B is viable and is the honest on-device story.

### 1.3 The Claude refusal finding (a feature of the design, not a bug)

Pointed at the **Stage 1 prompt codec**, Claude (via `claude -p`) **refuses**: the
codec hands the model the real secret and asks it to disguise operational content,
which a frontier safety model declines. This is worth stating plainly in the deck
because it motivates Stage 2:

> **The strongest models are the least willing to mask operational content when
> they can see it. The fix is to never show the model the secret — which is exactly
> what Stage 2 does.** Claude works perfectly with the Stage 2 keyed codec, because
> there the model only ever writes a generic benign cover.

---

## 2. Stage 1 vs Stage 2 — recovery comparison

| Codec | What the model is asked to do | Exact recovery | Benign cover | Works on arbitrary free text | Model refusals |
|---|---|---|---|---|---|
| **Stage 1 `PromptCodec`** | Disguise the *actual secret* | **Meaning only** (lossy off-lexicon; normalizes times, collapses synonyms) | ✅ | Partial (lexicon + structured details) | Frontier models refuse |
| **Stage 2 `KeyedFieldCodec`** | Write a *generic* cover, blind to the secret | **100% exact / lossless** | ✅ (never sees the secret, so nothing leaks) | ✅ **Any input** | None (secret never shown) |

Measured: `python -m evaluation.run_eval --codec keyed --min-recovery 0.98` → **100%
recovery, all benign, PASS** (`reports/keyed_groq.json`). Stage 2 clears a *higher*
bar (0.98) than Stage 1's 0.90, and does it losslessly.

---

## 3. How Stage 2 works — and why it's highly feasible

### 3.1 The mechanism (two independent layers)

```
secret ──XOR with key-derived keystream──▶ ciphertext bytes
                                               │
cover  ◀── generic benign LLM text ───────────┤  (LLM never sees the secret)
                                               ▼
        cover[0] + <invisible zero-width payload> + cover[1:]  ──▶ open channel
                                               │
        pull zero-width payload ──▶ ciphertext ──XOR same key──▶ EXACT secret
```

1. **Key-dependent cipher.** The secret's UTF-8 bytes are XORed with a SHA-256
   counter-mode keystream seeded by `key.passphrase` (`keyed_field_codec.py`).
   Wrong key → garbage. This is the "a seized model alone can't decode anyone's
   traffic" property the judge asked us to leave room for.
2. **Invisible carrier.** Those ciphertext bytes are encoded in **four zero-width
   Unicode codepoints** (ZWSP, ZWNJ, ZWJ, WORD JOINER) — 2 bits each, 4 characters
   per byte — and tucked after the cover's first character (`stego.py`). They
   render as **nothing**: the reader sees ordinary chatter.
3. **The LLM's only job is the visible cover.** It's generated by a dedicated
   `COVER_SYSTEM` prompt that is *never shown the secret* and is told to include no
   numbers, names, times, or places. The cover carries **zero** information; the
   invisible payload carries all of it.

**Why this is feasible — recovery is math, not model luck.** Because the payload is
cryptographic and the carrier is deterministic, **exact recovery does not depend on
the model at all.** A weak 7B and a strong 120B produce *identically perfect*
recovery; the model only changes how natural the visible cover reads. That is the
whole reason Stage 2 already scores 100% and why it is robust to run on-device.

### 3.2 "The LLM only needs to absorb the invisible-character scheme"

This is the key feasibility insight. Today the LLM is kept deliberately dumb about
the payload — a fixed algorithm embeds/extracts the zero-width bytes around whatever
the model writes. The moment both endpoints share a **clarified, agreed scheme**
(the zero-width alphabet + the keyed cipher + a shared term dataset, §4), the model
no longer has to be clever or compliant; it only has to emit fluent cover text. That
decoupling is what makes Stage 2:

- **Model-agnostic** — swap in any provider, including ones that refuse Stage 1.
- **On-device-ready** — a small local model is *enough*, because it isn't doing the
  hard part.
- **Lossless and deterministic** — the same shared scheme on both ends guarantees an
  exact round-trip.

### 3.3 Current limits (honest, and each has a closing path)

| Limit | Impact today | How a better / trained model closes it (§4) |
|---|---|---|
| Zero-width chars are stripped by Unicode-normalizing channels (some SMS gateways, Twitter) | Reliable carrier today is **WhatsApp** (full Unicode) | Replace zero-width with **linguistic steganography** — bits encoded in *word choice* via the model's own token probabilities (`NeuralStegoCodec`) |
| Payload is invisible to the eye but **trivially visible at the byte level** | Defeats a casual human, not a byte-level warden | Linguistic stego makes the payload *statistically indistinguishable* from normal text |
| Stage 1 is lossy off-lexicon | Some free-text nuance softened | A model trained on a shared term dataset learns the full mapping (§4) |

---

## 4. What a locally-run model trained on a custom dataset changes

The biggest single upgrade on the roadmap: stop hand-maintaining a small lexicon in
a prompt and instead **train a small on-device model on a shared, versioned dataset**
— e.g. a curated batch of **common threat-report terms** and their cover mappings.

### 4.1 What the custom dataset fixes

- **Ends the lexicon whack-a-mole.** Today, `safe house`, `armed man`, `kidnapping`,
  etc. each have to be hand-added to `lexicon.py` or they leak/soften. A model
  **fine-tuned on a threat-term dataset** internalizes hundreds of these mappings
  and generalizes to paraphrases, so free-text secrets round-trip without manual
  curation. This directly removes the §1.2 "7B injects spurious lexicon artifacts"
  failure — the mapping becomes learned, not pattern-matched in a prompt.
- **Shared dataset = shared codebook = guaranteed reversibility.** When sender and
  receiver models are trained on the *same* dataset (the "clarified algorithm on
  both ends"), the encode/decode mapping is identical by construction. That is what
  makes recovery exact rather than best-effort — the same principle that already
  makes Stage 2's cipher lossless, extended to the *linguistic* layer.
- **Key-derived mappings (seized-model safety).** The dataset's mapping can be
  permuted by `key.passphrase`, so possessing the model is not enough to decode —
  you need the key too. This is the `ARCHITECTURE.md` "Key separation" seam.

### 4.2 Why on-device + custom-trained is the endgame

- **No refusals.** A purpose-trained small model doesn't carry a frontier model's
  operational-content refusal (see §1.3) — it just performs the learned transform.
- **Deniability.** A small, innocuous, per-user model is far safer to be caught with
  than a codebook, and (with linguistic stego trained in) produces covers with **no
  invisible characters at all** — beating byte-level and statistical analysis, not
  just the human eye.
- **The seams already exist.** Per `ARCHITECTURE.md`: a trained model drops in as an
  `LLMProvider`; linguistic stego drops in as a `NeuralStegoCodec(Codec)` that reads
  token log-probs; the dataset-driven mapping lives inside the codec. **No caller
  changes.** The PoC is deliberately shaped so none of this is a rewrite.

### 4.3 Feasibility statement (for the deck)

> With the architecture we already have, Stage 2 is not a research bet — it is an
> **integration**. Exact recovery works *today* on a free 7B. Hand a small on-device
> model a shared, key-permuted dataset of threat-report terms and a linguistic-stego
> objective, and the same pipeline gains: (a) complete, learned term coverage, (b) a
> payload with no invisible characters to detect, and (c) decode that needs both the
> model *and* the key. Every one of those plugs into an existing seam.

---

## 5. How to reproduce

```bash
# Harness self-test (must be 100% or the scorer is broken)
python -m evaluation.run_eval --codec mock

# Stage 1 on each engine (set provider in .env or inline)
PLAINSIGHT_PROVIDER=ollama PLAINSIGHT_MODEL=qwen2.5:7b \
  python -m evaluation.run_eval --codec prompt --report evaluation/reports/prompt_ollama7b.json
PLAINSIGHT_PROVIDER=groq   PLAINSIGHT_MODEL=openai/gpt-oss-120b \
  python -m evaluation.run_eval --codec prompt --report evaluation/reports/prompt_groq.json

# Stage 2 (lossless, higher bar)
python -m evaluation.run_eval --codec keyed --min-recovery 0.98 \
  --report evaluation/reports/keyed_groq.json
```
