# Fellowship of the Workflows

A centralized repository for sharing AI agent workflows across your team. Works with Claude Code, Cursor, Copilot, Codex, Windsurf, Gemini, Roo, Goose, and more.

## What's Inside

| Type | Count | Description |
|------|-------|-------------|
| **Skills** | 55 | Executable packages — code review, Terraform, AWS, security audits, and more |
| **Rules** | 25 | Conditional context files — git safety, output style, coding patterns |
| **Agents** | 34 | Subagent definitions — specialist agents for focused tasks |
| **Hooks** | 5 | Claude Code event hooks — block dangerous commands, guard branches |
| **Personas** | 12 | AI personality overlays — Gandalf, Treebeard, and friends |
| **Starters** | 3 | Project templates — minimal, standard, full |

All workflows are authored once and automatically translated to each tool's native format on install.

## Quick Start

There are two ways to use this repo:

| | Plugin Mode | Install Mode |
|---|---|---|
| **How** | Load directly as a Claude Code plugin | Copy workflows into your project |
| **Tools** | Claude Code only | All 9 tools |
| **Components** | Skills, agents, hooks | Skills, agents, rules, starters, personas |
| **Setup** | One command | Per-workflow install |

### Option A: Claude Code Plugin (fastest)

```bash
# Load for a single session
claude --plugin-dir /path/to/fellowship-of-the-workflows

# Or install persistently (user scope — available in all projects)
claude plugin install /path/to/fellowship-of-the-workflows

# Or add to your project's .claude/settings.json (shared with team)
claude plugin install /path/to/fellowship-of-the-workflows --scope project
```

All 55 skills, 34 agents, and 5 hooks are auto-discovered. Use `/code-review`, `/terraform`, `/security-review`, etc. immediately.

> **Note:** Rules and starters still need `fotw install` — they must live in your project directory. See [Option B](#option-b-install-mode-any-tool).

### Option B: Install Mode (any tool)

```bash
# 1. Clone and set up the CLI
git clone https://github.com/TrevorEdris/fellowship-of-the-workflows.git
cd fellowship-of-the-workflows
./bin/bootstrap                    # Creates a project-local Python venv (3.10+ required)

# 2. See what's available
./bin/fotw list                    # Everything
./bin/fotw list --type skill       # Just skills
./bin/fotw list --tag aws          # Skills tagged "aws"
./bin/fotw list --tag review       # Skills tagged "review"

# 3. Install a starter template to your project
./bin/fotw install starters/standard ~/my-project --for claude-code

# 4. Install individual workflows
./bin/fotw install skills/code-review ~/my-project --for claude-code
./bin/fotw install rules/ai-session ~/my-project --for cursor
./bin/fotw install rules/git-safety --global --for claude-code   # Available in all projects
```

> **Which `--for` value do I use?** See [Supported Tools](#supported-tools) below.

## Commands

| Command | Description |
|---------|-------------|
| `./bin/bootstrap` | Set up the CLI environment (Python 3.10+ required) |
| `./bin/fotw list` | List available workflows |
| `./bin/fotw install` | Deploy a workflow or starter to a project |
| `./bin/fotw new` | Create a new workflow from template |
| `./bin/fotw validate` | Validate workflow files |

Run any command with `--help` for full options.

### Install Options

```bash
./bin/fotw install skills/code-review ~/my-project --for claude-code          # To a project
./bin/fotw install rules/ai-session --global --for cursor                     # Global (all projects)
./bin/fotw install --all ~/my-project --for claude-code --force               # Everything at once
./bin/fotw install skills/code-review ~/my-project --for claude-code --dry-run  # Preview only
```

| Flag | Description |
|------|-------------|
| `--for <tool>` | **Required.** Target tool (see table below) |
| `--global` / `-g` | Install to `~/.<tool>/` (available in all projects) |
| `--all` / `-a` | Install all workflows at once |
| `--force` / `-f` | Overwrite without prompting |
| `--dry-run` / `-n` | Preview what would be installed |
| `--to-claude-dir` | Place CLAUDE.md inside `.claude/` directory |

Without `--force`, the installer prompts before overwriting: `[o]verwrite / [s]kip / [d]iff / [b]ackup / [O]verwrite-all / [S]kip-all / [q]uit`.

### Supported Tools

| Tool | `--for` value | Config directory | Rule extension |
|------|---------------|------------------|----------------|
| Claude Code | `claude-code` | `.claude/` | `.md` |
| Cursor | `cursor` | `.cursor/` | `.mdc` |
| GitHub Copilot | `copilot` | `.github/` | `.instructions.md` |
| OpenAI Codex | `codex` | `.codex/` | `.md` |
| Windsurf | `windsurf` | `.windsurf/` | `.md` |
| Gemini Code Assist | `gemini` | `.gemini/` | `.md` |
| Roo Code | `roo` | `.roo/` | `.md` |
| Goose | `goose` | `.goose/` | `.md` |
| Universal | `universal` | `.ai/` | `.md` |

Use `--for both` to install for both Claude Code and Cursor simultaneously.

## Starter Templates

Starters give you a ready-made project config file with bundled rules.

```bash
./bin/fotw install starters/standard ~/my-project --for claude-code  # → CLAUDE.md
./bin/fotw install starters/standard ~/my-project --for cursor       # → AGENTS.md
./bin/fotw install starters/standard ~/my-project --for copilot      # → AGENTS.md + .github/instructions/
```

| Tier | Description | Bundled Rules |
|------|-------------|---------------|
| `minimal` | Git safety, output style (~20 lines) | `git-safety`, `output-style` |
| `standard` | + Discover → Plan → Implement workflow (~30 lines) | + `discover-plan-implement`, `ai-session` |
| `full` | + Persona system (12 characters), multi-repo safety (~40 lines) | + `multi-repo-safety`, `persona-integration` |

See [starters/README.md](starters/README.md) for details and modular snippets.

## Workflow Types

| Type | Storage | Description |
|------|---------|-------------|
| **Skills** | `skills/<name>/SKILL.md` | Executable packages ([Agent Skills](https://agentskills.io) standard) |
| **Rules** | `rules/*.mdc` | Conditional context files (Cursor format, auto-translated on install) |
| **Agents** | `agents/*.md` | Subagent definitions with tool restrictions |
| **Hooks** | `hooks/*.js` | Claude Code hook scripts (Claude Code only) |

Rules are authored in Cursor `.mdc` format and automatically translated to each tool's native format on install (e.g., `globs` → `paths` for Claude, `globs` → `applyTo` for Copilot).

### Skill Tags

Skills are categorized with tags for filtering. Use `./bin/fotw list --tag <tag>` to filter.

| Tag | Description | Count |
|-----|-------------|-------|
| `architecture` | System design, API design, patterns, databases | 8 |
| `infrastructure` | IaC, provisioning, containers, cloud resources | 8 |
| `documentation` | Docs generation, writing, diagrams | 7 |
| `meta` | Agent self-management, session tools, orchestration | 7 |
| `review` | Code, design, security, or performance review | 7 |
| `incident-response` | Alerting, on-call, incident management | 5 |
| `aws` | Amazon Web Services | 4 |
| `gcp` | Google Cloud Platform | 4 |
| `azure` | Microsoft Azure | 3 |
| `observability` | Monitoring instrumentation, dashboards, SLOs | 3 |
| `security` | Security hardening, IAM, vulnerability analysis | 3 |
| `testing` | TDD, E2E, test scaffolding, debugging | 3 |
| `ci-cd` | CI/CD pipelines, deployment automation | 1 |
| `git` | Git workflows, branching, PRs, commits | 1 |
| `go` | Go language patterns | 1 |
| `python` | Python language patterns | 1 |
| `rust` | Rust language patterns | 1 |
| `typescript` | TypeScript language patterns | 1 |

<details>
<summary><strong>Skills by Category</strong> (click to expand)</summary>

#### Infrastructure

| Skill | Tags | Description |
|-------|------|-------------|
| `aws-iac` | `aws`, `infrastructure` | Author, review, deploy, and migrate AWS infrastructu... |
| `azure-iac` | `azure`, `infrastructure` | Author, review, and deploy Azure infrastructure usin... |
| `cloud-run` | `gcp`, `infrastructure` | Deploy and operate Cloud Run services/jobs, Cloud Fu... |
| `docker` | `infrastructure` | Author Dockerfiles, Docker Compose configurations, a... |
| `kubernetes` | `infrastructure` | Author Kubernetes manifests, Helm charts, and Kustom... |
| `pulumi` | `infrastructure` | Build and manage multi-cloud infrastructure with Pul... |
| `terraform` | `infrastructure` | Write, review, refactor, and audit Terraform configu... |
| `terragrunt` | `infrastructure` | Design and implement DRY Terragrunt configurations u... |

#### Architecture

| Skill | Tags | Description |
|-------|------|-------------|
| `api-design` | `architecture` | Design REST and GraphQL APIs. Covers endpoint naming... |
| `aws-serverless` | `aws`, `architecture` | AWS serverless architecture patterns: Lambda functio... |
| `azure-functions` | `azure`, `architecture` | Azure Functions development guidance: trigger and bi... |
| `c4-architecture` | `architecture`, `documentation` | Generate architecture documentation using C4 model M... |
| `database-schema-designer` | `architecture` | Design SQL and NoSQL database schemas. Covers normal... |
| `event-driven` | `architecture` | Design event-driven architectures using message brok... |
| `gcp-data` | `gcp`, `architecture` | Design and operate GCP data stores: Cloud SQL (MySQL... |
| `system-design` | `architecture` | Design and review distributed system architecture. C... |

#### Review

| Skill | Tags | Description |
|-------|------|-------------|
| `accessibility-audit` | `review` | WCAG 2.1/2.2 accessibility audit covering all POUR p... |
| `code-review` | `review` | Perform thorough code review on a PR using the Pragm... |
| `design-review` | `review` | Design review for front-end code changes using Playw... |
| `performance-optimization` | `review` | Analyze code for performance bottlenecks including N... |
| `refactoring` | `review` | Systematic code refactoring with smell detection, sa... |
| `security-review` | `security`, `review` | Perform security-focused code review to identify HIG... |
| `work-review` | `review` | Review work accomplished over a time period by corre... |

#### Documentation

| Skill | Tags | Description |
|-------|------|-------------|
| `agent-md-refactor` | `documentation`, `meta` | Refactor bloated AGENTS.md, CLAUDE.md, or similar ag... |
| `c4-architecture` | `architecture`, `documentation` | Generate architecture documentation using C4 model M... |
| `desloppify` | `documentation` | Identify and remove AI slop from code comments, docu... |
| `mermaid-diagrams` | `documentation` | Comprehensive guide for creating software diagrams u... |
| `reverse-engineer` | `documentation` | Extract PRDs, design docs, and architecture diagrams... |
| `update-docs` | `documentation` | Sync documentation with code changes. Detects stale ... |
| `writing-clearly-and-concisely` | `documentation` | Use when writing prose humans will read—documentatio... |

#### Meta

| Skill | Tags | Description |
|-------|------|-------------|
| `agent-md-refactor` | `documentation`, `meta` | Refactor bloated AGENTS.md, CLAUDE.md, or similar ag... |
| `create-persona` | `meta` | Create a new AI assistant persona interactively. Sup... |
| `orchestrate` | `meta` | Coordinate multiple subagents to complete a large ta... |
| `plan-validator` | `meta` | Validate implementation plans for completeness, spec... |
| `session-handoff` | `meta` | Creates handoff documents for AI agent session trans... |
| `session-index` | `meta` | Generate and maintain a session index with cross-ses... |
| `switch-persona` | `meta` | Switch AI assistant personas interactively. Lists av... |

#### Incident Response

| Skill | Tags | Description |
|-------|------|-------------|
| `better-stack` | `observability`, `incident-response` | Better Stack specialist. Configures Better Stack's u... |
| `grafana-irm` | `observability`, `incident-response` | Grafana Cloud IRM specialist. Configures Grafana IRM... |
| `incident-io` | `incident-response` | incident.io specialist. Configures incident.io for S... |
| `incident-management` | `incident-response` | Cross-platform incident management router. Detects t... |
| `pagerduty` | `incident-response` | Configure PagerDuty services, escalation policies, o... |

#### Cloud Platforms

| Skill | Tags | Description |
|-------|------|-------------|
| `aws` | `aws` | AWS credential setup, SDK patterns (Go/Python/TypeSc... |
| `aws-iac` | `aws`, `infrastructure` | Author, review, deploy, and migrate AWS infrastructu... |
| `aws-iam` | `aws`, `security` | AWS security patterns: IAM policy design, least-priv... |
| `aws-serverless` | `aws`, `architecture` | AWS serverless architecture patterns: Lambda functio... |
| `azure` | `azure` | Azure platform guidance covering authentication (Man... |
| `azure-functions` | `azure`, `architecture` | Azure Functions development guidance: trigger and bi... |
| `azure-iac` | `azure`, `infrastructure` | Author, review, and deploy Azure infrastructure usin... |
| `cloud-run` | `gcp`, `infrastructure` | Deploy and operate Cloud Run services/jobs, Cloud Fu... |
| `gcp` | `gcp` | GCP project setup, authentication (ADC/Workload Iden... |
| `gcp-data` | `gcp`, `architecture` | Design and operate GCP data stores: Cloud SQL (MySQL... |
| `gcp-iam` | `gcp`, `security` | Audit and configure GCP IAM: roles/bindings, service... |

#### Security

| Skill | Tags | Description |
|-------|------|-------------|
| `aws-iam` | `aws`, `security` | AWS security patterns: IAM policy design, least-priv... |
| `gcp-iam` | `gcp`, `security` | Audit and configure GCP IAM: roles/bindings, service... |
| `security-review` | `security`, `review` | Perform security-focused code review to identify HIG... |

#### Testing

| Skill | Tags | Description |
|-------|------|-------------|
| `e2e-testing` | `testing` | Scaffold E2E and integration tests using Playwright.... |
| `systematic-debugging` | `testing` | Structured root-cause analysis for bugs, test failur... |
| `test-driven-development` | `testing` | Enforce RED-GREEN-REFACTOR cycle for any implementat... |

#### Observability

| Skill | Tags | Description |
|-------|------|-------------|
| `better-stack` | `observability`, `incident-response` | Better Stack specialist. Configures Better Stack's u... |
| `grafana-irm` | `observability`, `incident-response` | Grafana Cloud IRM specialist. Configures Grafana IRM... |
| `observability` | `observability` | Instrument, audit, and configure observability for s... |

#### Other

| Skill | Tags | Description |
|-------|------|-------------|
| `cicd-pipeline` | `ci-cd` | Generate, optimize, and manage CI/CD pipelines for G... |
| `git-workflow` | `git` | Interactive git workflow assistant. Generates conven... |
| `go-patterns` | `go` | Go patterns and idioms. Use when writing, reviewing,... |
| `python-patterns` | `python` | Python patterns and idioms. Use when writing, review... |
| `rust-patterns` | `rust` | Rust patterns and idioms. Use when writing, reviewin... |
| `typescript-patterns` | `typescript` | TypeScript patterns and idioms. Use when writing, re... |

</details>

### Hooks (Claude Code only)

Hooks are Node.js scripts that intercept Claude Code events at runtime — blocking dangerous commands, protecting secrets, guarding branches, etc. No other AI tool supports hooks.

```bash
# List available hooks
./bin/fotw list --type hook

# Install all hooks globally
./bin/fotw install hooks --global --for claude-code

# Install a single hook
./bin/fotw install hooks/branch-guard --global --for claude-code

# Include test files alongside hooks
./bin/fotw install hooks --global --for claude-code --include-tests

# Preview without installing
./bin/fotw install hooks --global --for claude-code --dry-run
```

Hooks require `--global` and `--for claude-code`. The installer copies scripts to `~/.claude/hooks/` and merges hook configuration into `~/.claude/settings.json` (with backup).

Each hook script contains a `@fotw-hook` metadata tag in its JSDoc header that declares its event, matcher, and description.

### Claude Code Plugin Architecture

This repo is structured as a [Claude Code plugin](https://code.claude.com/docs/en/plugins-reference). When loaded via `claude --plugin-dir` or `claude plugin install`, Claude Code auto-discovers:

| Component | Location | Discovery |
|-----------|----------|-----------|
| Skills | `skills/*/SKILL.md` | Auto — available as `/skill-name` slash commands |
| Agents | `agents/*.md` | Auto — Claude invokes based on task context |
| Hooks | `hooks/hooks.json` | Auto — registered as event handlers |
| Rules | `rules/*.mdc` | **Manual** — requires `fotw install` to copy to project |
| Starters | `starters/*.md` | **Manual** — requires `fotw install` to copy to project |

The `.claude-plugin/plugin.json` manifest declares the plugin metadata. Hook scripts use `${CLAUDE_PLUGIN_ROOT}` to resolve paths relative to the plugin directory.

Skills and agents support additional Claude Code fields (`model`, `argument-hint`, `disable-model-invocation`, `user-invocable`) that are ignored by other tools. See [CONTRIBUTING.md](CONTRIBUTING.md) for the full schema.

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines on adding new workflows.

## License

MIT
