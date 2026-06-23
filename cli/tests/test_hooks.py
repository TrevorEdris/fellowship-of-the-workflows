"""Tests for hook scanning, settings merging, and installation."""

import json
from pathlib import Path

import pytest

from fotw.models.workflow import Hook, WorkflowType
from fotw.services.catalog import _parse_hook_meta, scan_hooks, validate_hook
from fotw.services.installer import InstallContext
from fotw.services.settings_merger import (
    build_hooks_config,
    merge_hooks,
    read_settings,
    write_settings,
)


# ---------------------------------------------------------------------------
# Scan / parse
# ---------------------------------------------------------------------------


def test_scan_hooks_returns_list():
    hooks = scan_hooks()
    assert isinstance(hooks, list)
    assert len(hooks) == 6
    names = [h.name for h in hooks]
    assert "block-dangerous-commands" in names
    assert "context-snapshot" in names
    assert "persona-context" in names
    assert "plan-validator-reminder" in names
    assert "protect-secrets" in names
    assert "session-reminder" in names


def test_scan_hooks_have_events():
    hooks = scan_hooks()
    for h in hooks:
        assert h.event, f"Hook {h.name} has no event"


def test_parse_hook_meta(tmp_path: Path):
    script = tmp_path / "test.js"
    script.write_text(
        '#!/usr/bin/env node\n'
        '/**\n'
        ' * @fotw-hook {"event":"PreToolUse","matcher":"Bash","description":"Test hook"}\n'
        ' */\n'
    )
    meta = _parse_hook_meta(script)
    assert meta is not None
    assert meta["event"] == "PreToolUse"
    assert meta["matcher"] == "Bash"
    assert meta["description"] == "Test hook"


def test_parse_hook_meta_missing(tmp_path: Path):
    script = tmp_path / "no-meta.js"
    script.write_text("#!/usr/bin/env node\nconsole.log('hello');\n")
    meta = _parse_hook_meta(script)
    assert meta is None


# ---------------------------------------------------------------------------
# Hook model
# ---------------------------------------------------------------------------


def test_hook_workflow_id():
    h = Hook(name="my-hook", description="test", event="PreToolUse", matcher="Bash")
    assert h.workflow_id == "hooks/my-hook"


def test_hook_settings_entry():
    h = Hook(name="block-dangerous-commands", description="test",
             event="PreToolUse", matcher="Bash")
    entry = h.settings_entry
    assert "hooks" in entry
    assert entry["hooks"][0]["type"] == "command"
    assert "block-dangerous-commands.js" in entry["hooks"][0]["command"]
    assert entry["matcher"] == "Bash"


def test_hook_settings_entry_no_matcher():
    h = Hook(name="context-snapshot", description="test",
             event="PreCompact", matcher="")
    entry = h.settings_entry
    assert "matcher" not in entry


# ---------------------------------------------------------------------------
# Settings merger
# ---------------------------------------------------------------------------


def test_build_hooks_config():
    hooks = [
        Hook(name="a", description="", event="PreToolUse", matcher="Bash"),
        Hook(name="b", description="", event="PreToolUse", matcher="Edit"),
        Hook(name="c", description="", event="PreCompact", matcher=""),
    ]
    config = build_hooks_config(hooks)
    assert "PreToolUse" in config
    assert len(config["PreToolUse"]) == 2
    assert "PreCompact" in config
    assert len(config["PreCompact"]) == 1


def test_merge_hooks_empty():
    hooks = [
        Hook(name="test", description="", event="PreToolUse", matcher="Bash"),
    ]
    result = merge_hooks({}, hooks)
    assert "hooks" in result
    assert "PreToolUse" in result["hooks"]
    assert len(result["hooks"]["PreToolUse"]) == 1


def test_merge_hooks_existing():
    """Re-merging the same hooks should not create duplicates."""
    hooks = [
        Hook(name="test", description="", event="PreToolUse", matcher="Bash"),
    ]
    first = merge_hooks({}, hooks)
    second = merge_hooks(first, hooks)
    assert len(second["hooks"]["PreToolUse"]) == 1


def test_merge_hooks_preserves_keys():
    existing = {
        "env": {"FOO": "bar"},
        "statusLine": "custom",
        "enabledPlugins": ["test"],
    }
    hooks = [
        Hook(name="test", description="", event="PreToolUse", matcher="Bash"),
    ]
    result = merge_hooks(existing, hooks)
    assert result["env"] == {"FOO": "bar"}
    assert result["statusLine"] == "custom"
    assert result["enabledPlugins"] == ["test"]
    assert "hooks" in result


def test_read_settings_missing(tmp_path: Path):
    result = read_settings(tmp_path / "nonexistent.json")
    assert result == {}


def test_read_settings_valid(tmp_path: Path):
    f = tmp_path / "settings.json"
    f.write_text('{"hooks": {}}')
    result = read_settings(f)
    assert result == {"hooks": {}}


def test_write_settings(tmp_path: Path):
    f = tmp_path / "settings.json"
    write_settings({"hooks": {"PreToolUse": []}}, f)
    assert f.is_file()
    content = f.read_text()
    assert content.endswith("\n")
    parsed = json.loads(content)
    assert parsed["hooks"]["PreToolUse"] == []


# ---------------------------------------------------------------------------
# Validation
# ---------------------------------------------------------------------------


def test_validate_hooks_pass():
    hooks = scan_hooks()
    for h in hooks:
        result = validate_hook(h.path)
        assert result.ok, f"Hook {h.name} failed validation: {result.errors}"


def test_validate_hook_missing_meta(tmp_path: Path):
    script = tmp_path / "bad.js"
    script.write_text("#!/usr/bin/env node\nconsole.log('no meta');\n")
    result = validate_hook(script)
    assert not result.ok
    assert any("@fotw-hook" in e for e in result.errors)


# ---------------------------------------------------------------------------
# Install guards
# ---------------------------------------------------------------------------


def test_install_rejects_non_claude():
    from fotw.services.installer import install_hooks
    ctx = InstallContext(tool="cursor", target_repo=Path.home(), is_global=True)
    assert not install_hooks(ctx)


def test_install_rejects_non_global():
    from fotw.services.installer import install_hooks
    ctx = InstallContext(tool="claude-code", target_repo=Path("/tmp/test"), is_global=False)
    assert not install_hooks(ctx)


# ---------------------------------------------------------------------------
# WorkflowType
# ---------------------------------------------------------------------------


def test_workflow_type_hook():
    assert WorkflowType.from_str("hook") == WorkflowType.HOOK
    assert WorkflowType.from_str("hooks") == WorkflowType.HOOK


# ---------------------------------------------------------------------------
# Has tests detection
# ---------------------------------------------------------------------------


def test_scan_hooks_detect_tests():
    hooks = scan_hooks()
    hooks_with_tests = [h for h in hooks if h.has_tests]
    names = [h.name for h in hooks_with_tests]
    assert "context-snapshot" in names
    assert "session-reminder" in names
