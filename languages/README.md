# languages/

Language-specific workflows for Go, Python, TypeScript, and Rust.

Not auto-discovered in plugin mode. Install explicitly.

## Contents

```
languages/
├── skills/       Language-specific skills
└── rules/        Language-specific rules
```

## Skills

| Skill | Description |
|-------|-------------|
| `go-patterns` | Go patterns and idioms: error handling, interfaces, concurrency |
| `python-patterns` | Python patterns and idioms: typing, dataclasses, async |
| `typescript-patterns` | TypeScript patterns and idioms: generics, utility types, strict mode |
| `rust-patterns` | Rust patterns and idioms: ownership, error handling, concurrency |

## Rules

| Rule | Description |
|------|-------------|
| `go-patterns` | Go error handling, interfaces, concurrency patterns |
| `python-patterns` | Python typing, dataclasses, async patterns, testing idioms |
| `typescript-patterns` | TypeScript strict mode, utility types, async patterns |
| `rust-patterns` | Rust error handling, ownership idioms, concurrency patterns |

## Install

```bash
# Install a skill
./bin/fotw install languages/skills/go-patterns ~/my-project --for claude-code

# Install a rule
./bin/fotw install languages/rules/go-patterns ~/my-project --for claude-code

# Install all language workflows for a given language
./bin/fotw install languages/skills/typescript-patterns ~/my-project --for claude-code
./bin/fotw install languages/rules/typescript-patterns ~/my-project --for claude-code
```

## Why separate?

Not everyone writes Go. Not everyone writes Rust. Language-specific workflows in the core `skills/` and `rules/` directories would add noise for users working in a different stack. Install only what your team uses.
