"""ClaudeCliProvider plumbing, with subprocess faked (no CLI call)."""
import subprocess

import pytest

from plainsight.config import Settings
from plainsight.providers import get_provider
from plainsight.providers import claude_cli_provider as mod
from plainsight.providers.claude_cli_provider import ClaudeCliProvider


class _Result:
    def __init__(self, returncode, stdout, stderr=""):
        self.returncode, self.stdout, self.stderr = returncode, stdout, stderr


def test_complete_builds_command_and_returns_text(monkeypatch):
    captured = {}

    def fake_run(cmd, **kwargs):
        captured["cmd"] = cmd
        captured["kwargs"] = kwargs
        return _Result(0, "  a benign cover \n")

    monkeypatch.setattr(mod.subprocess, "run", fake_run)
    p = ClaudeCliProvider(model="sonnet", binary="claude")

    assert p.complete("SYSTEM PROMPT", "USER TEXT") == "a benign cover"
    cmd = captured["cmd"]
    assert cmd[0] == "claude" and "-p" in cmd and "USER TEXT" in cmd
    assert cmd[cmd.index("--system-prompt") + 1] == "SYSTEM PROMPT"
    assert cmd[cmd.index("--model") + 1] == "sonnet"
    assert "--restricted" in cmd
    # runs in a neutral cwd so it doesn't auto-load the project's CLAUDE.md
    assert captured["kwargs"].get("cwd")


def test_nonzero_exit_raises(monkeypatch):
    monkeypatch.setattr(mod.subprocess, "run", lambda cmd, **kw: _Result(1, "", "boom"))
    with pytest.raises(RuntimeError, match="exit 1"):
        ClaudeCliProvider(binary="claude").complete("s", "u")


def test_empty_output_raises(monkeypatch):
    monkeypatch.setattr(mod.subprocess, "run", lambda cmd, **kw: _Result(0, "   "))
    with pytest.raises(RuntimeError, match="empty"):
        ClaudeCliProvider(binary="claude").complete("s", "u")


def test_timeout_raises(monkeypatch):
    def boom(cmd, **kw):
        raise subprocess.TimeoutExpired(cmd, 1)
    monkeypatch.setattr(mod.subprocess, "run", boom)
    with pytest.raises(RuntimeError, match="timed out"):
        ClaudeCliProvider(binary="claude").complete("s", "u")


def test_factory_builds_claude_cli_provider():
    s = Settings(provider="claude-cli", model="sonnet", temperature=0.0,
                 anthropic_api_key=None, openai_api_key=None)
    assert isinstance(get_provider(s), ClaudeCliProvider)
