# Starter Templates

Quickstart templates for configuring AI coding assistants in your projects.

## Tool Support

| Tool | Output File | Standard |
|------|-------------|----------|
| Claude Code | `CLAUDE.md` | Claude-specific |
| Cursor | `AGENTS.md` | [Universal standard](https://agents.md/) |
| GitHub Copilot | `AGENTS.md` | Universal standard |
| Other tools | `AGENTS.md` | Universal standard |

Both files use identical content — only the filename differs.

## Choose Your Tier

| Tier | Lines | Best For |
|------|-------|----------|
| `minimal` | ~25 | Quick setup, small projects |
| `standard` | ~55 | Most projects (recommended) |
| `full` | ~115 | Power users, multi-repo workspaces, persona support |

## Installation

```bash
# For Claude Code users
./bin/install starters/standard ~/my-project --for claude-code

# For Cursor users (creates AGENTS.md)
./bin/install starters/standard ~/my-project --for cursor

# For teams with mixed tooling (creates both files)
./bin/install starters/standard ~/my-project --for both

# Install CLAUDE.md to .claude/ directory instead of project root
./bin/install starters/standard ~/my-project --for claude-code --to-claude-dir
```

Then edit the template to fill in your project-specific details.

## Tier Comparison

### Minimal
- Project overview placeholder
- Tech stack placeholder
- Build commands placeholder
- Git safety rules
- Output style guidelines

### Standard (Recommended)
Everything in Minimal, plus:
- Discover → Plan → Implement workflow
- Session documentation pattern
- Enhanced git safety

### Full
Everything in Standard, plus:
- Persona system integration (12 personas available)
- Multi-repo safety rules
- Repository map for workspaces
- Required session documentation

## Modular Snippets

Prefer to build your own? Mix and match from `snippets/`:

| Snippet | Purpose |
|---------|---------|
| `workflow-discover-plan-implement.md` | Structured workflow phases |
| `session-documentation.md` | Session tracking for complex tasks |
| `git-safety.md` | Safe git practices |
| `output-style.md` | Concise, professional output |
| `persona-integration.md` | Enable the persona system |
| `persona-config-example.yaml` | Config file template |

## What Each Section Does

### Project Overview / Tech Stack / Build Commands
Helps the AI understand your project context. Fill in your specific details.

### Workflow: Discover → Plan → Implement
Prevents the AI from jumping straight to code. Enforces:
1. **Discover** — Understand before changing
2. **Plan** — Get approval before implementing
3. **Implement** — Execute with minimal diffs

### Session Documentation
Creates an audit trail in `.ai/sessions/` for complex tasks. Useful for:
- Handoffs between sessions
- Reviewing decisions later
- Multi-step implementations

### Git Safety
Prevents common accidents:
- No direct commits to main/master
- No accidental credential commits
- Branch awareness before changes

### Output Style
Reduces verbose AI patterns:
- Skip filler phrases
- Use bullets over paragraphs
- State facts directly

## Persona System

Add personality to your AI assistant with themed personas. Each persona provides:
- **Voice Guide** — Speech patterns, tone, signature phrases
- **Thematic Mappings** — Dev concepts mapped to the character's world
- **Static Elements** — Consistent phase names and severity levels
- **Contextual Guidance** — How to respond in different situations
- **Example Quotes** — Fallback pool for inspiration

### Available Personas

| ID | Source | Vibe |
|----|--------|------|
| `gandalf` | Lord of the Rings | Wise wizard, patient mentor |
| `yoda` | Star Wars | Inverted syntax, cryptic wisdom |
| `picard` | Star Trek: TNG | Commanding presence, diplomatic |
| `the-dude` | Big Lebowski | Laid-back, philosophical slacker |
| `princess-bride` | The Princess Bride | Quotable adventure, wit |
| `spock` | Star Trek | Logical, analytical, precise |
| `bob-ross` | Joy of Painting | Encouraging, positive, gentle |
| `mr-rogers` | Mister Rogers | Kind, thoughtful, nurturing |
| `attenborough` | Nature docs | Documentary narration, wonder |
| `ron-swanson` | Parks & Rec | Minimalist, anti-bureaucracy |
| `monty-python` | Monty Python | Absurdist British humor |
| `chewbacca` | Star Wars | RRWWWWGGG (unintelligible loyalty) |

### Enabling a Persona

1. **Add the integration snippet** to your CLAUDE.md/AGENTS.md:
   - Copy content from `snippets/persona-integration.md`

2. **Create a config file** in your project:
   ```yaml
   # .claude/persona.yaml (for Claude Code)
   # .cursor/persona.yaml (for Cursor)

   persona: gandalf
   intensity: noticeable
   ```

3. **Intensity Levels:**
   | Level | Behavior |
   |-------|----------|
   | `off` | Standard professional responses |
   | `minimal` | Flavor at key moments only |
   | `noticeable` | Light flavor in most responses (recommended) |
   | `excessive` | Full character immersion |

### Creating Custom Personas

Use `personas/_template.md` as a starting point. Key sections:
1. Voice Guide — Define how the character speaks
2. Thematic Mappings — Map dev concepts to their world
3. Static Elements — Set phase names and severity levels
4. Contextual Guidance — Define behavior for different situations
5. Example Quotes — Provide reference material

See existing personas in `personas/` for examples
