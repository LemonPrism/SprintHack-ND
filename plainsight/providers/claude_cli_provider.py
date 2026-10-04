"""Claude via the Claude Code CLI (`claude -p`), using your Claude subscription.

No API key: this shells out to the locally-installed `claude` binary in print mode,
which authenticates with your logged-in Pro/Max session. It's the "use Claude for
free" path — stronger covers and reliable arbitrary themes/personas for the Stage 1
PromptCodec, without the per-token API billing of AnthropicProvider.

Trade-offs (documented honestly): no temperature/seed control (determinism is out of
the MVP's scope), ~seconds of latency per call (a process launch), and it drives a
coding CLI to do text generation. Recovery in the keyed codec does not use the LLM,
so this only affects how natural the *cover* reads.

The CLI runs from a neutral working directory so it does not auto-load this project's
CLAUDE.md, and with --restricted so no code/shell tools are available.
"""
from __future__ import annotations
import shutil
import subprocess
import tempfile

from .base import LLMProvider


class ClaudeCliProvider(LLMProvider):
    def __init__(self, model: str = "sonnet", binary: str | None = None,
                 timeout: float = 120.0, cwd: str | None = None):
        self._bin = binary or shutil.which("claude") or "claude"
        self._model = model
        self._timeout = timeout
        self._cwd = cwd or tempfile.gettempdir()  # neutral cwd: no project CLAUDE.md

    def complete(self, system: str, user: str, *, temperature: float | None = None) -> str:
        # temperature is accepted for interface parity but the CLI exposes no knob.
        cmd = [self._bin, "-p", user,
               "--system-prompt", system,
               "--output-format", "text",
               "--restricted"]
        if self._model:
            cmd += ["--model", self._model]
        try:
            result = subprocess.run(
                cmd, capture_output=True, text=True, encoding="utf-8",
                timeout=self._timeout, cwd=self._cwd,
            )
        except FileNotFoundError as e:
            raise RuntimeError(
                "Claude CLI not found. Install Claude Code and run `claude` once to log "
                "in, or set PLAINSIGHT_CLAUDE_BIN to its path."
            ) from e
        except subprocess.TimeoutExpired as e:
            raise RuntimeError(f"Claude CLI timed out after {self._timeout}s.") from e

        if result.returncode != 0:
            raise RuntimeError(
                f"Claude CLI failed (exit {result.returncode}): "
                f"{(result.stderr or '').strip()[:300]}"
            )
        out = (result.stdout or "").strip()
        if not out:
            raise RuntimeError("Claude CLI returned empty output.")
        return out
