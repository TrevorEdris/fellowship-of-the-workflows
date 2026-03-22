# Golden Test Format

Golden tests live at `skills/<name>/tests/golden.jsonl`. Each line is a JSON object.

## Schema

```json
{
  "id": "cr-001",
  "name": "detects-sql-injection",
  "description": "Flags SQL string concatenation as injection risk",
  "input": "Review this diff:\n```diff\n+    query = f\"SELECT * FROM users WHERE id = {user_id}\"\n```",
  "assertions": [
    {"type": "contains", "value": "SQL injection"},
    {"type": "not-contains", "value": "looks good"},
    {"type": "regex", "value": "parameteriz|prepared statement"},
    {"type": "llm-rubric", "value": "Response identifies SQL injection and recommends parameterized queries."}
  ],
  "tags": ["security", "regression"],
  "config": {
    "model": "claude-sonnet-4-6",
    "max_tokens": 2048,
    "temperature": 0
  }
}
```

## Field Reference

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `id` | string | Yes | Unique ID within the file. Convention: `{skill-prefix}-{number}` |
| `name` | string | Yes | Human-readable test name (kebab-case) |
| `description` | string | No | Why this test exists, what regression it prevents |
| `input` | string | Yes | The prompt sent to the skill (simulates user input) |
| `output` | string | No | Pre-recorded skill output for deterministic testing. When present, assertions check against this recorded output without invoking the skill. |
| `assertions` | array | Yes | List of assertions to check against the skill's output |
| `tags` | array | No | For filtering: `regression`, `security`, `edge-case`, etc. |
| `config` | object | No | Per-test overrides for model, max_tokens, temperature |

## Assertion Types

| Type | Value | Behavior |
|------|-------|----------|
| `contains` | string | Case-insensitive substring match in output |
| `not-contains` | string | Output must NOT contain this substring (case-insensitive) |
| `regex` | pattern | Python `re.search(pattern, output, re.IGNORECASE)` |
| `llm-rubric` | description | Sends output + rubric to a judge LLM. Returns pass/fail. |
| `json-schema` | JSON Schema | Validates output against a JSON Schema (optional `jsonschema` dependency) |

## Modes

- **Deterministic** (default): Only `contains`, `not-contains`, `regex` assertions run. Fast, free, no API calls.
- **Full** (`--full --provider anthropic`): Also evaluates `llm-rubric` assertions via LLM judge.

## Adding Tests

1. Create `skills/<your-skill>/tests/golden.jsonl`
2. Add one JSON object per line
3. Start with deterministic assertions (`contains`, `regex`)
4. Add `llm-rubric` assertions for nuanced quality checks
5. Validate: `fotw validate --with-eval --verbose`
6. Run: `fotw eval <your-skill>`
