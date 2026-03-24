# Fellowship of the Workflows

A complete AI agent workflow system for software engineering. Author workflows once, use them across Claude Code, Cursor, Copilot, and 6 more tools — no copy-paste, no per-tool maintenance. Single source, multi-target.

---

## Installation

### Claude Code Plugin (recommended)

```bash
# Register the marketplace (one-time)
/plugin marketplace add TrevorEdris/fellowship-of-the-workflows

# Install the plugin
/plugin install fotw@fellowship-of-the-workflows
```

All core skills, agents, and hooks are auto-discovered immediately. Use `/code-review`, `/security-review`, `/terraform`, etc.

> **Rules** need to live in your project directory. Use `fotw setup` to install them:
> ```bash
> git clone https://github.com/TrevorEdris/fellowship-of-the-workflows.git
> cd fellowship-of-the-workflows && ./bin/bootstrap
> ./bin/fotw setup ~/my-project --for claude-code
> ```

### Install Mode (any tool)

For non-Claude tools or selective installation:

```bash
git clone https://github.com/TrevorEdris/fellowship-of-the-workflows.git
cd fellowship-of-the-workflows
./bin/bootstrap                                                     # Python 3.10+ required

./bin/fotw list                                                     # See what's available
./bin/fotw install skills/code-review ~/my-project --for cursor     # Individual skill
./bin/fotw install rules/git-safety --global --for claude-code      # Global rule
```

Run any command with `--help` for full options.

---

## Updating

### Plugin Mode

```bash
/plugin                                           # Check for updates
/plugin update fotw@fellowship-of-the-workflows   # Apply update
```

### Install Mode

```bash
cd fellowship-of-the-workflows && git pull
./bin/fotw update ~/my-project                    # Re-sync changed rules
```

---

## Uninstalling

### Plugin Mode

```bash
/plugin uninstall fotw@fellowship-of-the-workflows
```

### Install Mode

Remove the files installed by `fotw install` or `fotw setup` from your project's config directory (e.g., `.claude/rules/`, `.cursor/rules/`). Check `.fotw-lock.json` in your project root for the full list of installed files.

---

## What You Get

- **Review & quality** — code review, security review, design review, performance analysis, chaos review, accessibility audit
- **Architecture & design** — system design, API design, database schemas, event-driven architecture, C4 diagrams
- **Infrastructure** — Terraform, Pulumi, Kubernetes, Docker, AWS/Azure/GCP services
- **Development workflow** — TDD enforcement, git workflow, CI/CD pipelines, session management, plan validation
- **Incident response** — PagerDuty, Grafana IRM, incident.io, Better Stack (auto-detected routing)
- **Language patterns** — Go, Python, Rust, TypeScript (skills + rules)

Full listing: [docs/CATALOG.md](docs/CATALOG.md)

---

## How It Works

Rules are authored once in Cursor `.mdc` format. On install, the translator rewrites frontmatter for the target tool — `globs` becomes `paths` for Claude Code, `applyTo` for Copilot, stripped for tools that only support plain Markdown. The rule body is preserved exactly.

Skills are instruction documents invoked as slash commands. Agents are specialist subprocesses that execute focused tasks in isolation. Skills may invoke agents and synthesize results.

For full architecture details, see [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md).

---

## Hooks (Claude Code only)

Hooks are Node.js scripts that intercept Claude Code events — blocking dangerous commands, protecting secrets, guarding branches.

```bash
./bin/fotw install hooks --global --for claude-code    # Install all hooks
```

Hooks require `--global` and `--for claude-code`. The installer copies scripts to `~/.claude/hooks/` and merges configuration into `~/.claude/settings.json`.

---

## Supported Tools

| Tool | `--for` value | Config directory |
|------|---------------|------------------|
| Claude Code | `claude-code` | `.claude/` |
| Cursor | `cursor` | `.cursor/` |
| GitHub Copilot | `copilot` | `.github/` |
| OpenAI Codex | `codex` | `.codex/` |
| Windsurf | `windsurf` | `.windsurf/` |
| Gemini Code Assist | `gemini` | `.gemini/` |
| Roo Code | `roo` | `.roo/` |
| Goose | `goose` | `.goose/` |
| Universal | `universal` | `.ai/` |

Use `--for both` to install for both Claude Code and Cursor simultaneously.

---

## Workflow Tiers

| Tier | Location | Plugin Auto-Discovery |
|------|----------|-----------------------|
| **Core** | `skills/`, `rules/`, `agents/` | Yes |
| **Languages** | `languages/` | No — explicit install |
| **Platforms** | `platforms/` | No — explicit install |
| **Vendors** | `vendors/` | No — explicit install |

Install only what your team uses. All tiers follow the same quality bar.

See [languages/README.md](languages/README.md), [platforms/README.md](platforms/README.md), and [vendors/README.md](vendors/README.md) for full listings.

---

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines on adding new workflows.

## License

MIT
