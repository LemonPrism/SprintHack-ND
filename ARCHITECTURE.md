# ARCHITECTURE.md — how PlainSight is built to grow

The MVP is deliberately small, but it is shaped so every long-term feature is a
**drop-in**, not a rewrite. This file maps each future feature to the exact seam
where it plugs in.

## The two seams

```
            secret text
                │
                ▼
        ┌───────────────┐        uses        ┌────────────────┐
        │     Codec     │ ─────────────────▶ │   LLMProvider  │
        │ (how to mask) │                     │ (where text    │
        └───────────────┘                     │  comes from)   │
                │                              └────────────────┘
                ▼
          benign cover  ──▶ open channel ──▶  Codec.unmask ──▶ secret
```

- **`LLMProvider`** (`plainsight/providers/base.py`): one method,
  `complete(system, user, *, temperature) -> str`. Swap the *source* of text.
- **`Codec`** (`plainsight/codecs/base.py`): `mask(secret, *, key, theme) -> cover`
  and `unmask(cover, *, key, theme) -> secret`. Swap the *method* of masking.
- **`SharedKey`** (`plainsight/key.py`): the shared secret both sides hold. Today
  a passphrase + theme; it already exposes a seeded RNG for future keyed schemes.

Callers (`cli.py`, `evaluation/run_eval.py`) depend **only** on these interfaces,
obtained through the factories `providers.get_provider()` and `codecs.get_codec()`.
Add a class, register it in the factory, done.

## Current implementations

| Kind      | Class                  | Status | Notes                                           |
|-----------|------------------------|--------|-------------------------------------------------|
| Provider  | `AnthropicProvider`    | live   | cloud; needs a paid API key                     |
| Provider  | `OllamaProvider`       | live   | local & free (`qwen2.5:7b`); no API key         |
| Provider  | `MockProvider`         | live   | canned output; unit-test plumbing only          |
| Codec     | `PromptCodec`          | live   | Stage 1 — pure-LLM mask/unmask (the MVP)        |
| Codec     | `ReversibleMockCodec`  | live   | lossless; the harness's self-test               |
| Codec     | `KeyedFieldCodec`      | live   | Stage 2 — lossless, key-dependent; invisible zero-width payload |

## Where each long-term feature plugs in

- **On-device local models** → `OllamaProvider(LLMProvider)` in
  `providers/` (**done** — the PoC runs on it), registered in `get_provider`. *No codec changes.* This is why the
  judge's "pretend it's local" framing costs us nothing — the seam is already there.
- **Multilingual** → add a `language` field to `SharedKey` and reference it in the
  encode/decode prompts. No interface change.
- **Pattern / determinism mitigation** → use `SharedKey.rng()` (already present,
  seeded by the passphrase) to vary cover choices reproducibly on both ends; raise
  `temperature` behind a codec flag. Lives entirely inside a codec.
- **Objective benign-ness scoring** → `evaluation/score.py` isolates the benign
  check. Replace `trigger_word` matching with a `BenignScorer` (perplexity under a
  reference model, or an LLM-judge). The harness interface stays the same.
- **Traffic blending (metadata angle)** → a `Codec` that takes a sample of real
  channel messages and conditions the cover on them. Still just a `Codec`.
- **Image / photo carriers** → a `Codec` whose `cover` is an image caption or an
  image path; the `LLMProvider` can be multimodal. Interfaces unchanged.
- **Key separation / seized-model safety** → put the real secret in the keyed
  payload (`fields.pack_fields`) encrypted/obfuscated with `SharedKey`, so the
  model alone can't decode. This is a `KeyedFieldCodec` concern only.
- **Neural linguistic steganography** (Meteor/Discop-style bit-level stego) → a
  `NeuralStegoCodec(Codec)` that needs a provider exposing token log-probs; add
  that capability to a provider subclass. Mention in the deck as "known alternative."

## Data contract for the eval harness

`evaluation/cases.json` is a list of:
```json
{
  "id": "shahed-factory",
  "secret": "…the clandestine message…",
  "must_recover": ["48.4647", "Viktor Orlov", "Sunday"],
  "trigger_words": ["drone", "destroy", "bomb"]
}
```
- `must_recover`: substrings that MUST reappear in the unmasked output (scores recovery).
- `trigger_words`: substrings that must NOT appear in the cover (scores benign-ness).

Add cases freely; keep `shahed-factory` as the regression anchor.

## Invariants (don't break these)
1. Callers touch interfaces only — never import a concrete codec/provider directly.
2. `ReversibleMockCodec` stays lossless — it validates the scorer.
3. `fields.pack_fields` / `unpack_fields` stay exact inverses.
4. Encode/decode default to `temperature=0` until the pattern-mitigation feature lands.
