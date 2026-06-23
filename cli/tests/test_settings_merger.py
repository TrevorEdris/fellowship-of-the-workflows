"""Tests for persona-related settings merging (outputStyle, spinnerVerbs)."""

from fotw.services.settings_merger import (
    PERSONA_STYLE_PREFIX,
    capture_previous,
    merge_env,
    merge_output_style,
    merge_spinner_verbs,
    remove_persona_keys,
)

BASE_SETTINGS = {
    "permissions": {"allow": ["Bash(git status)"]},
    "hooks": {"PreToolUse": [{"matcher": "Bash", "hooks": [{"command": "x"}]}]},
    "env": {"FOO": "bar"},
}


def test_merge_output_style_sets_key_and_preserves_others():
    merged = merge_output_style(dict(BASE_SETTINGS), "Persona: Gandalf")
    assert merged["outputStyle"] == "Persona: Gandalf"
    assert merged["permissions"] == BASE_SETTINGS["permissions"]
    assert merged["hooks"] == BASE_SETTINGS["hooks"]
    assert merged["env"] == BASE_SETTINGS["env"]


def test_merge_spinner_verbs_replace_mode():
    merged = merge_spinner_verbs(dict(BASE_SETTINGS), ["Whittling", "Grilling"])
    assert merged["spinnerVerbs"] == {"mode": "replace", "verbs": ["Whittling", "Grilling"]}
    assert merged["permissions"] == BASE_SETTINGS["permissions"]


def test_capture_previous_records_user_values_once():
    settings = {"outputStyle": "Explanatory", "spinnerVerbs": {"mode": "append", "verbs": ["Pondering"]}}
    record = capture_previous(settings, {})
    assert record["previous-output-style"] == "Explanatory"
    assert record["previous-spinner-verbs"] == {"mode": "append", "verbs": ["Pondering"]}


def test_capture_previous_records_absence_as_none():
    record = capture_previous({}, {})
    assert record["previous-output-style"] is None
    assert record["previous-spinner-verbs"] is None


def test_capture_previous_skips_fotw_written_values():
    """Switching persona A -> B must not clobber the original user record."""
    settings = {"outputStyle": f"{PERSONA_STYLE_PREFIX}Gandalf", "spinnerVerbs": {"mode": "replace", "verbs": ["Conjuring"]}}
    record = capture_previous(settings, {"previous-output-style": "Explanatory", "previous-spinner-verbs": None})
    assert record["previous-output-style"] == "Explanatory"
    assert record["previous-spinner-verbs"] is None


def test_capture_previous_no_record_when_fotw_active_and_no_prior_record():
    settings = {"outputStyle": f"{PERSONA_STYLE_PREFIX}Gandalf"}
    record = capture_previous(settings, {})
    assert "previous-output-style" not in record
    assert "previous-spinner-verbs" not in record


def test_remove_persona_keys_restores_recorded_values():
    settings = {
        "outputStyle": f"{PERSONA_STYLE_PREFIX}Gandalf",
        "spinnerVerbs": {"mode": "replace", "verbs": ["Conjuring"]},
        "env": {"FOO": "bar"},
    }
    record = {
        "previous-output-style": "Explanatory",
        "previous-spinner-verbs": {"mode": "append", "verbs": ["Pondering"]},
    }
    result = remove_persona_keys(settings, record)
    assert result["outputStyle"] == "Explanatory"
    assert result["spinnerVerbs"] == {"mode": "append", "verbs": ["Pondering"]}
    assert result["env"] == {"FOO": "bar"}


def test_remove_persona_keys_deletes_when_no_previous():
    settings = {
        "outputStyle": f"{PERSONA_STYLE_PREFIX}Gandalf",
        "spinnerVerbs": {"mode": "replace", "verbs": ["Conjuring"]},
    }
    record = {"previous-output-style": None, "previous-spinner-verbs": None}
    result = remove_persona_keys(settings, record)
    assert "outputStyle" not in result
    assert "spinnerVerbs" not in result


def test_remove_persona_keys_leaves_user_changes_untouched():
    """If the user manually switched styles after activation, do not clobber."""
    settings = {"outputStyle": "Explanatory", "spinnerVerbs": {"mode": "replace", "verbs": ["Conjuring"]}}
    record = {"previous-output-style": "Learning", "previous-spinner-verbs": None}
    result = remove_persona_keys(settings, record)
    assert result["outputStyle"] == "Explanatory"
    assert result["spinnerVerbs"] == {"mode": "replace", "verbs": ["Conjuring"]}


def test_merge_env_preserves_existing_keys():
    """Regression: merge_env previously had no test coverage."""
    merged = merge_env({"env": {"A": "1"}, "outputStyle": "Default"}, {"B": "2"})
    assert merged["env"] == {"A": "1", "B": "2"}
    assert merged["outputStyle"] == "Default"
