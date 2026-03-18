# CI Integration for Evals

## Quick Start

Add to your CI pipeline after `fotw validate`:

```yaml
# GitHub Actions example
- name: Validate workflows
  run: ./bin/fotw validate --with-eval --verbose

- name: Run deterministic evals
  run: ./bin/fotw eval --all --output eval-results.json
```

## Modes

### Deterministic (default, free)

```bash
fotw eval --all
```

Runs `contains`, `not-contains`, and `regex` assertions only. No API calls, no cost, fast.

### Full (requires API key)

```bash
fotw eval --all --full --provider anthropic
```

Also evaluates `llm-rubric` assertions using an LLM judge. Requires `ANTHROPIC_API_KEY` environment variable.

## Commands

```bash
# Validate golden test syntax
fotw validate --with-eval --verbose

# Run all skills with golden tests
fotw eval --all

# Run a single skill
fotw eval code-review

# Filter by tag
fotw eval --all --tag security

# JSON output for CI artifacts
fotw eval --all --output eval-results.json
```

## Exit Codes

- `0` — All assertions passed (or deferred in deterministic mode)
- `1` — One or more assertions failed

## Recommended CI Strategy

1. **Always run:** `fotw validate --with-eval` (syntax check, fast)
2. **Always run:** `fotw eval --all` (deterministic assertions)
3. **Optional:** `fotw eval --all --full --provider anthropic` (LLM-rubric, costs money)

Keep deterministic assertions as the CI gate. Use `--full` mode for periodic quality audits or pre-release checks.
