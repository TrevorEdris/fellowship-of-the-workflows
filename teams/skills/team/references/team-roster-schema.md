# Team Roster Schema

Team rosters are YAML files that define predefined Agent Team compositions.

## Required Fields

| Field | Type | Description |
|-------|------|-------------|
| `name` | string | Roster identifier (must match filename stem) |
| `description` | string | What this team does and when to use it |
| `lead_model` | string | Model for the team lead (`opus`, `sonnet`, `haiku`) |
| `team_size` | integer | Number of teammates (must match length of `teammates` list) |
| `coordination` | string | How teammates should interact and sequence their work |
| `teammates` | list | Teammate definitions (see below) |

## Teammate Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `name` | string | yes | Unique name for this teammate within the team |
| `agent` | string | yes | Agent name — must match a file in `agents/*.md` |
| `model` | string | yes | Model tier: `opus`, `sonnet`, or `haiku` |
| `focus` | string | yes | What this teammate should focus on (injected as primary directive) |
| `plan_approval` | boolean | yes | Whether the lead must approve this teammate's plan before they implement |

## Constraints

- `team_size` must be >= 2 (a team of one is just a subagent)
- Each `agent` value must reference an existing agent definition
- Teammate `name` values must be unique within the roster
