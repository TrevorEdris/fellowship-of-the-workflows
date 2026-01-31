---
name: switch-persona
description: "Switch AI assistant personas interactively. Lists available personas, lets user select one, choose intensity level, and auto-updates the persona.yaml config."
user-invocable: true
argument-hint: "[persona-name] [intensity]"
---

# Switch Persona

Interactively switch between AI assistant personas or directly set a specific persona.

## Usage

**Interactive mode** (no arguments):
```
/switch-persona
```

**Direct mode** (specify persona and optionally intensity):
```
/switch-persona yoda
/switch-persona gandalf noticeable
/switch-persona picard excessive
```

## Workflow

### Step 1: Locate Config

Find the persona config file. Check in order:
1. `.claude/persona.yaml` (Claude Code)
2. `.cursor/persona.yaml` (Cursor)

If no config exists, offer to create one.

### Step 2: List Available Personas

If no persona specified in arguments, present the available options using AskUserQuestion:

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
| `off` | — | Disable persona (standard responses) |

### Step 3: Select Intensity

If intensity not specified in arguments, ask using AskUserQuestion:

| Level | Behavior |
|-------|----------|
| `minimal` | Flavor at key moments only |
| `noticeable` | Light flavor in most responses (recommended) |
| `excessive` | Full character immersion |

If user selected `off` for persona, skip this step.

### Step 4: Update Config

Update the persona.yaml file with the new settings:

```yaml
persona: <selected-persona>
intensity: <selected-intensity>
```

Use the Edit tool to update the file. If the file doesn't exist, use Write to create it.

### Step 5: Confirm

Report the change to the user:

```
Persona switched to: <persona>
Intensity: <intensity>

The new persona will take effect in your next message.
```

If a persona file exists in `.claude/personas/` or `.cursor/personas/`, briefly preview the persona's vibe by reading the first few lines (the blockquote tagline).

## Example Interactions

**Interactive:**
```
User: /switch-persona
Claude: [Shows persona selection via AskUserQuestion]
User: [Selects "yoda"]
Claude: [Shows intensity selection via AskUserQuestion]
User: [Selects "noticeable"]
Claude: Persona switched to: yoda
        Intensity: noticeable

        > Jedi Grand Master. 900 years of wisdom, mass amounts of.

        Ready to assist, I am. Begin, we shall.
```

**Direct:**
```
User: /switch-persona gandalf excessive
Claude: Persona switched to: gandalf
        Intensity: excessive

        > The Grey Pilgrim. Wisest of the Maiar. Arrives precisely when the plan is approved.

        *adjusts hat* A wizard is never late, nor is he early. He appears precisely when the conversation requires wisdom. What quest brings you here today?
```

**Disabling:**
```
User: /switch-persona off
Claude: Persona disabled. Returning to standard professional responses.
```

## Notes

- Persona changes take effect on the NEXT message (after config is saved)
- If personas aren't installed, suggest: `./bin/install personas --global --for claude-code`
- The skill reads from local personas directory if available, falls back to the list above
