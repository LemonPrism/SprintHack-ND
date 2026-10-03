# PlainSight

Masking & unmasking of plaintext with generative AI — a codebook replacement.
DIU "AI-Enhanced Resilient Communications" track, SprintHack@ND 2026.

**New here? Read `CLAUDE.md`, then `TASKS.md`, then `ARCHITECTURE.md`.**

## Quickstart
```bash
python -m venv .venv && source .venv/bin/activate   # Windows: .venv/Scripts/activate
pip install -r requirements.txt
cp .env.example .env     # defaults to local Ollama: install it, then `ollama pull qwen2.5:7b`
                         # (or switch to anthropic and add ANTHROPIC_API_KEY)

python -m plainsight.cli mask "Meet at the docks at 2300 Friday." --theme "dinner plans"
python -m plainsight.cli unmask "<benign message>" --theme "dinner plans"
```

## Verify
```bash
pytest -q
python -m evaluation.run_eval --codec mock     # must be 1.00 (harness self-test)
python -m evaluation.run_eval --codec prompt   # real masking (Ollama running, or an Anthropic key)
```

## Live demo
```bash
streamlit run demo/app.py      # http://localhost:8501
```
Three panes: sender / what an eavesdropper sees / receiver. See `demo/README.md`
for the pre-pitch checklist (warm up the model, use the book-swap preset).

Fictional test data only. Defensive / anti-censorship PoC.
