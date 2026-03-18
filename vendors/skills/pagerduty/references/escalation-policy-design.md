# Escalation Policy Design

Escalation policies determine who gets paged, in what order, and when escalation triggers. One policy per team, not per service.

---

## Standard Three-Level Policy

```
Level 1: On-call engineer
  - Acknowledge timeout: 5 minutes
  - If no ack → escalate to Level 2

Level 2: Team lead
  - Acknowledge timeout: 15 minutes
  - If no ack → escalate to Level 3

Level 3: Manager / Director
  - Acknowledge timeout: 30 minutes
  - If no ack → repeat Level 3 (or stop — configure per team)
```

**Hard rule:** Never assign more than 2 escalation levels for a single service. Three levels is the maximum for a team. More levels slow resolution — after L2 fails, the issue is organizational.

---

## Terraform Resource

```hcl
resource "pagerduty_escalation_policy" "team_payments" {
  name      = "payments-team"
  num_loops = 2  # Repeat the entire policy this many times before giving up

  rule {
    escalation_delay_in_minutes = 5

    target {
      type = "schedule_reference"
      id   = pagerduty_schedule.payments_primary.id
    }
  }

  rule {
    escalation_delay_in_minutes = 15

    target {
      type = "schedule_reference"
      id   = pagerduty_schedule.payments_secondary.id
    }
  }

  rule {
    escalation_delay_in_minutes = 30

    target {
      type = "user_reference"
      id   = data.pagerduty_user.engineering_manager.id
    }
  }
}
```

---

## On-Call Schedule Structure

### Recommended Layer Pattern

```
Schedule: payments-primary
├── Layer 1 (Primary rotation)
│   ├── Rotation: weekly
│   ├── Handoff: Monday 09:00 local
│   └── Engineers: [alice, bob, charlie, dave]
└── Layer 2 (Shadow/secondary)
    ├── Rotation: weekly, offset by one slot
    ├── Same engineers, different order
    └── Purpose: backup coverage + on-call training
```

### Terraform Resource

```hcl
resource "pagerduty_schedule" "payments_primary" {
  name      = "payments-primary-on-call"
  time_zone = "America/New_York"

  layer {
    name                         = "Primary Rotation"
    start                        = "2025-01-06T09:00:00-05:00"
    rotation_virtual_start       = "2025-01-06T09:00:00-05:00"
    rotation_turn_length_seconds = 604800  # 7 days

    users = [
      data.pagerduty_user.alice.id,
      data.pagerduty_user.bob.id,
      data.pagerduty_user.charlie.id,
      data.pagerduty_user.dave.id,
    ]
  }

  layer {
    name                         = "Shadow Rotation"
    start                        = "2025-01-06T09:00:00-05:00"
    rotation_virtual_start       = "2025-01-13T09:00:00-05:00"  # offset by 1 week
    rotation_turn_length_seconds = 604800

    users = [
      data.pagerduty_user.bob.id,
      data.pagerduty_user.charlie.id,
      data.pagerduty_user.dave.id,
      data.pagerduty_user.alice.id,
    ]
  }
}
```

---

## Schedule Coverage Validation Checklist

Before publishing a new schedule, verify all of these:

- [ ] No coverage gaps > 15 minutes at any point in the rotation cycle
- [ ] At least 2 people are always reachable (primary + shadow layer)
- [ ] No single person is on rotation for more than 5 consecutive days
- [ ] Handoff time does not fall on a weekend (unless the team agrees)
- [ ] All engineers have confirmed their schedule in PD (accepted the invitation)
- [ ] Override calendar is accessible to all team members for personal time off

### Gap Detection (PagerDuty API)

Use the `GET /schedules/{id}/users` endpoint with a `since`/`until` range to detect gaps:

```bash
curl -H "Authorization: Token token=$PD_API_TOKEN" \
  "https://api.pagerduty.com/schedules/$SCHEDULE_ID/users?since=2025-01-01T00:00:00Z&until=2025-04-01T00:00:00Z" \
  | jq '.users | length'
# If 0 at any window, there is a gap
```

---

## Auto-Resolve Timeout by Criticality

Configure `auto_resolve_timeout` on the PD service (not the escalation policy):

| Criticality | `auto_resolve_timeout` | `acknowledgement_timeout` |
|-------------|----------------------|--------------------------|
| Critical (P1) | `null` (disabled) | `null` (disabled) |
| High (P2) | `14400` (4 hours) | `1800` (30 min) |
| Medium (P3) | `7200` (2 hours) | `600` (10 min) |
| Low (P4) | `3600` (1 hour) | `300` (5 min) |

```hcl
resource "pagerduty_service" "payments" {
  name                    = "payments-service"
  escalation_policy       = pagerduty_escalation_policy.team_payments.id
  auto_resolve_timeout    = 14400  # 4 hours — P2
  acknowledgement_timeout = 1800   # 30 minutes
  alert_creation          = "create_alerts_and_incidents"

  alert_grouping_parameters {
    type = "time"
    config {
      timeout = 300  # Group alerts within 5-minute window
    }
  }
}
```

---

## Alert Grouping

### Time-Based Grouping

Groups alerts from the same service that arrive within a configurable time window (in seconds). Prevents alert storms from cascading failures from generating hundreds of separate incidents.

- Recommended window: 300 seconds (5 minutes)
- Use when: multiple monitoring rules can fire simultaneously for the same root cause

### Content-Based (Intelligent) Grouping

Groups alerts that share the same `dedup_key` family or similar payload content.

- Use when: you have fine-grained alert rules that logically belong to one incident
- Requires PD AIOps license in some account tiers

### Choosing Between Them

Use time-based grouping as the default. Use content-based grouping only when you have distinct alert rules that should always produce one incident (e.g., multiple database connection errors from different pods that all indicate a single DB outage).
