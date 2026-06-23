---
description: Remind to bump plugin version when modifying plugin-included files.
globs: "agents/**,hooks/**,skills/**,output-styles/**,.claude-plugin/plugin.json"
alwaysApply: false
---

## Plugin Version Bump

When modifying files in `agents/`, `hooks/`, `skills/`, or `output-styles/`, bump the `version` field in `.claude-plugin/plugin.json` before committing.

### Semver Rules

- **Patch** (`x.y.Z`) — bug fixes, permission changes, minor hook/skill tweaks
- **Minor** (`x.Y.0`) — new skills, agents, or hooks; new features in existing ones
- **Major** (`X.0.0`) — breaking changes to existing skill/agent/hook interfaces

CI will fail if plugin-included files changed without a version bump.
