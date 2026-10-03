# CLAUDE.md — PlainSight

> Persistent context for Claude Code. **Read this first in every session.**
> Then read `TASKS.md` (what to build, in order) and `ARCHITECTURE.md`
> (how to extend it). Keep this file updated as the source of truth.

---

## What this is

**PlainSight** is a proof-of-concept for the DIU **"AI-Enhanced Resilient
Communications"** track at SprintHack@ND 2026. It replaces a physical/digital
codebook with a generative model.

A sensitive ("clandestine") message is **masked** into a benign-looking,
everyday message, sent over an open channel (SMS / WhatsApp / Twitter), and
**unmasked** by the recipient back into the original — or close enough to be
usable.

Example:
- Secret: *"The Shahed drone factory is at 48.4647 N, 35.0462 E. Workday
  0800–1700. Plant manager is Viktor Orlov. Destroy it Sunday."*
- Masked: *"Hey! Don't forget Viktor's birthday party Sunday — cake at 8,
  wrap up by 5. Address is on the group chat."*
- Unmasked → back to the secret.

## Why (threat model, one paragraph)

The adversary is a **nation-state that reads all plaintext** on open channels
(lawful intercept, the Great Firewall, compelled disclosure from providers).
Encryption does **not** help here: an AES-256 blob is a random-looking string,
and "who is sending unreadable traffic" is exactly what gets someone detained —
the **"bugged-hotel problem"** (you don't read every room, you watch for the
room that goes quiet). A physical/digital **codebook is self-incriminating**: if
the carrier is caught, the book proves they are an asset and exposes every past
message and every other collaborator. PlainSight's bet: a small, innocuous,
**deniable** model is far safer to be caught with than a codebook, and produces
traffic that looks like ordinary chatter.

## MVP definition — this is what we are graded on

The judge is **James ("Nick") Ashworth, DIU** (PhD, RF exploitation; he is the
sole judge, no formal rubric). He defined the MVP in his own words:

> Type in a string → the model produces a benign surface message with no
> actionable/suspicious wording → a decoder (a second model, the same model,
> or an inverted prompt) regenerates the original message, or close enough to
> be usable.

He said he judges on: **feasibility, closeness to this MVP, future
improvements, and honest acknowledgment of challenges.**

**The MVP is DONE when:**
1. `python -m evaluation.run_eval --codec prompt` runs the frozen test cases, and
2. aggregate **field-recovery ≥ `--min-recovery` (default 0.90)**, and
3. every masked message contains **none** of that case's `trigger_words`.

## Explicitly OUT of scope for the MVP — the judge's own carve-outs (all LATER)

Do **not** spend MVP time on these. They are the long-term backlog in `TASKS.md`:
- grammatical perfection
- multiple languages
- blending with *surrounding* message traffic (just look benign to a casual human)
- defeating statistical / pattern analysis (same input → same output is fine for now)
- running locally on-device — **a cloud model is explicitly fine for the PoC**
- You may assume both parties already share context **and the key**.

## The final solution (the vision everything must leave room for)

Small, **per-user, on-device** models that both mask and unmask, **keyed** so
that possessing the model alone cannot decode anyone's traffic, deployable to
at-risk people living under censorship. Nothing in the MVP may hard-close the
door on this — see `ARCHITECTURE.md`.

---

## Repository map

```
plainsight/
├── CLAUDE.md            ← you are here (project source of truth)
├── TASKS.md             ← staged plan + per-stage acceptance checks
├── ARCHITECTURE.md      ← extension points for every long-term feature
├── README.md            ← human quickstart
├── requirements.txt
├── .env.example         ← copy to .env, add your API key
├── conftest.py          ← puts repo root on sys.path for pytest
├── plainsight/          ← the package
│   ├── config.py        ← settings from env (.env)
│   ├── key.py           ← the shared secret / scheme (SharedKey)
│   ├── cli.py           ← `python -m plainsight.cli mask|unmask`
│   ├── providers/       ← WHERE text comes from (swappable)
│   │   ├── base.py          LLMProvider interface
│   │   ├── anthropic_provider.py
│   │   ├── ollama_provider.py    local & free (no API key)
│   │   └── mock_provider.py
│   ├── codecs/          ← HOW masking works (swappable)
│   │   ├── base.py          Codec interface
│   │   ├── prompt_codec.py       Stage 1 — real LLM mask/unmask (MVP)
│   │   ├── reversible_mock_codec.py  lossless test double for the harness
│   │   ├── fields.py             deterministic field extract/pack (Stage 2 core)
│   │   └── keyed_field_codec.py  Stage 2 — fidelity layer (scaffold + TODO)
│   └── prompts/         ← encode/decode system prompts (edit these a lot)
│       └── lexicon.py        shared sensitive->cover word table, rendered into both prompts
├── evaluation/          ← the verification harness (our "does it work?" gate)
│   ├── cases.json           frozen test cases incl. shahed-factory
│   ├── score.py             field-recovery + benign-ness scoring
│   └── run_eval.py          `python -m evaluation.run_eval`
├── tests/               ← pytest: plumbing + deterministic logic
└── demo/                ← Stage 3 UI lives here
```

## The one design rule that makes the long-term features possible

There are **two interfaces** and you swap implementations behind them:

- **`LLMProvider`** — *where* text comes from (cloud now, local Ollama later).
- **`Codec`** — *how* masking works (prompt-only now, keyed-field next,
  neural-stego / image-carrier later).

**New capability = new `Provider` or new `Codec` subclass.** Never bake a
provider or codec specific into a caller. The CLI and the eval harness only ever
touch the interfaces. This is the whole reason we can add local models,
multilingual, pattern-mitigation, etc. later without a rewrite.

## Run it

```bash
python -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env            # defaults to the free local Ollama provider
ollama pull qwen2.5:7b          # one-time model download (~4.7 GB); needs Ollama installed
# (or set PLAINSIGHT_PROVIDER=anthropic + ANTHROPIC_API_KEY in .env for the cloud model)

# manual round-trip with the real model:
python -m plainsight.cli mask   "Meet me at the docks at 2300 on Friday." --theme "dinner plans"
python -m plainsight.cli unmask "<the benign message it printed>"        --theme "dinner plans"
```

## Verify your work — run after EVERY change

```bash
pytest -q                                        # plumbing + deterministic logic, no API key
python -m evaluation.run_eval --codec mock       # MUST report 100% recovery (proves the harness)
python -m evaluation.run_eval --codec prompt     # real masking (local Ollama, or ANTHROPIC_API_KEY)
```

- The `mock` codec is lossless by construction; if it is ever < 100%, the
  **harness itself** is broken — fix that before trusting any `prompt` numbers.
- **Never** commit a change that regresses the `shahed-factory` case.

## Conventions & guardrails

- **Provider:** the team has no paid API key, so the PoC runs on the local
  `OllamaProvider` (`qwen2.5:7b`). This doubles as the on-device story.
- **Secrets:** API keys live in `.env` only. Never hard-code or commit them.
  `.env` is git-ignored.
- **Determinism:** encode/decode run at `temperature=0`. Keep it that way for
  the MVP (pattern-randomization is a later feature, see `TASKS.md`).
- **Stages:** follow `TASKS.md` in order. Do not mark a task done until its
  listed acceptance command passes.
- **Keep the test double honest:** `ReversibleMockCodec` must stay lossless.
- **Scope & ethics:** this is a sanctioned hackathon PoC with a defensive,
  anti-censorship / asset-protection purpose. Use **fictional test data only**
  (the cases provided are invented). Do not add real operational detail.
