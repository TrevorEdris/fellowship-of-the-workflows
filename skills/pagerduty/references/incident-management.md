# Incident Management

PagerDuty incident lifecycle, priority tiers, response automation, and postmortem workflows.

---

## Priority Tiers

Define priority tiers consistently across all services. Use the `pagerduty_priority` resource to enforce naming:

| Priority | Criteria | Response | SLA |
|----------|----------|----------|-----|
| P1 | Customer-facing outage, revenue impact, data loss | All-hands, immediate | Ack in 5 min, resolve in 1h |
| P2 | Degraded service, partial customer impact | On-call engineer | Ack in 15 min, resolve in 4h |
| P3 | Non-critical degradation, no immediate customer impact | Next business day | Resolve in 24h |
| P4 | Low-impact, informational | Backlog | Resolve in 1 week |

```hcl
resource "pagerduty_priority" "p1" {
  name        = "P1"
  color       = "#FF0000"
  description = "Critical — customer-facing outage or data loss"
}

resource "pagerduty_priority" "p2" {
  name        = "P2"
  color       = "#FF6600"
  description = "High — degraded service with partial customer impact"
}

resource "pagerduty_priority" "p3" {
  name        = "P3"
  color       = "#FFAA00"
  description = "Medium — non-critical, next-day response"
}

resource "pagerduty_priority" "p4" {
  name        = "P4"
  color       = "#0066FF"
  description = "Low — informational, backlog"
}
```

---

## Incident Workflows

Incident workflows automate standard response steps triggered by state transitions. As of 2025, there is no Terraform resource for incident workflows — configure via PD UI or REST API.

### Common Workflow Triggers

| Trigger | Common Actions |
|---------|---------------|
| Incident opened (P1) | Post to `#incidents` Slack, create Jira ticket, start Zoom bridge |
| Incident opened (P2) | Post to `#on-call` Slack, create Jira ticket |
| Incident acknowledged | Post "being investigated" to Slack |
| Incident resolved | Post resolution summary to Slack, close Jira ticket |

### API: Create Workflow

```bash
curl -X POST "https://api.pagerduty.com/incident_workflows" \
  -H "Authorization: Token token=$PD_API_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "incident_workflow": {
      "name": "P1 Response - Slack + Jira",
      "description": "Auto-posts to Slack and creates Jira ticket for P1 incidents",
      "trigger": {
        "type": "incident_event",
        "condition": "incident.priority == \"P1\" AND incident.status == \"triggered\""
      },
      "steps": [
        {
          "name": "Post to Slack",
          "action": {
            "id": "pagerduty.com:incident-workflows:send-status-update:1",
            "inputs": [
              {"name": "message", "value": "P1 incident opened: {{incident.title}}"}
            ]
          }
        }
      ]
    }
  }'
```

---

## Runbook Automation via Webhooks

PD incident state changes send webhooks that can trigger automated remediation.

### Webhook Payload (PD v3 webhook format)

```json
{
  "event": {
    "id": "evt_01ABC...",
    "event_type": "incident.triggered",
    "occurred_at": "2025-01-15T14:30:00Z",
    "agent": {...},
    "client": "PagerDuty",
    "data": {
      "id": "Q1ABC...",
      "type": "incident",
      "summary": "Error rate > 5% for payments-service",
      "status": "triggered",
      "priority": {"id": "P1", "name": "P1"},
      "service": {"id": "P1AB2CD", "summary": "payments-service"},
      "teams": [...],
      "custom_fields": {}
    }
  }
}
```

### Lambda Webhook Receiver Pattern

```python
import json
import hmac
import hashlib
import boto3

def handler(event, context):
    body = event['body'].encode()
    signature = event['headers'].get('X-PagerDuty-Signature', '')

    # Verify signature
    secret = get_secret('pd-webhook-secret')
    expected = hmac.new(secret.encode(), body, hashlib.sha256).hexdigest()
    if not hmac.compare_digest(f"v1={expected}", signature):
        return {'statusCode': 401, 'body': 'Invalid signature'}

    payload = json.loads(body)
    event_type = payload['event']['event_type']
    incident_id = payload['event']['data']['id']

    # Idempotency: check if already processed
    if already_processed(incident_id, event_type):
        return {'statusCode': 200, 'body': 'Already processed'}

    if event_type == 'incident.triggered':
        service = payload['event']['data']['service']['summary']
        if 'payments' in service:
            restart_payments_pods()  # Automated remediation

    mark_processed(incident_id, event_type)
    return {'statusCode': 200, 'body': 'OK'}
```

---

## Stakeholder Notifications (Subscribers)

Notify business stakeholders on high-severity incidents without paging them:

```bash
# Subscribe stakeholders to a service (they receive updates, not pages)
curl -X POST "https://api.pagerduty.com/services/$SERVICE_ID/subscribers" \
  -H "Authorization: Token token=$PD_API_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "subscribers": [
      {"type": "user_reference", "id": "$BUSINESS_OWNER_USER_ID"}
    ],
    "subscriber_objects": [{"type": "service_reference", "id": "$SERVICE_ID"}]
  }'
```

---

## Postmortem Automation

PD generates a postmortem template from the incident timeline. Capture the minimum viable postmortem immediately at resolution — quality degrades rapidly.

### Required Timeline Data Points

| Event | Source |
|-------|--------|
| First symptom (customer or monitoring) | PD incident timeline |
| Alert triggered time | PD incident `triggered_at` |
| First acknowledgment time | PD incident `first_ack_at` |
| Escalation events | PD incident log entries |
| Resolution time | PD incident `resolved_at` |
| Responders | PD incident `assignments` |

### PD Postmortem API

```bash
# Retrieve incident timeline for postmortem
curl "https://api.pagerduty.com/incidents/$INCIDENT_ID/log_entries?include[]=incident" \
  -H "Authorization: Token token=$PD_API_TOKEN" \
  | jq '.log_entries[] | {time: .created_at, type: .type, summary: .summary}'
```

### Postmortem Template (Minimum Viable)

```markdown
## Incident Summary
- **Incident ID:** [PD incident ID]
- **Service:** [affected service]
- **Priority:** [P1/P2]
- **Duration:** [triggered_at → resolved_at]
- **Customer Impact:** [description of impact]

## Timeline
| Time (UTC) | Event |
|------------|-------|
| [time] | First symptom observed |
| [time] | Alert triggered in PD |
| [time] | On-call engineer acknowledged |
| [time] | Root cause identified |
| [time] | Fix deployed |
| [time] | Incident resolved |

## Root Cause
[One paragraph: what failed, why it failed, why monitoring detected it when it did]

## Contributing Factors
- [Factor 1]
- [Factor 2]

## Action Items
| Item | Owner | Due Date |
|------|-------|----------|
| [Corrective action] | [@owner] | [date] |
```

### Confluence Integration via Webhook

```python
import requests

def create_confluence_postmortem(incident_data: dict, pd_timeline: list) -> str:
    """Creates a Confluence page from PD incident data."""
    body = build_postmortem_body(incident_data, pd_timeline)

    response = requests.post(
        "https://yourorg.atlassian.net/wiki/rest/api/content",
        auth=("user@example.com", CONFLUENCE_API_TOKEN),
        json={
            "type": "page",
            "title": f"Postmortem: {incident_data['summary']} ({incident_data['id']})",
            "space": {"key": "POSTMORTEMS"},
            "body": {
                "storage": {
                    "value": body,
                    "representation": "storage"
                }
            }
        }
    )
    return response.json()["_links"]["webui"]
```

---

## On-Call API: Who Is Currently On Call?

```bash
# Who is on call for a specific schedule right now?
curl "https://api.pagerduty.com/oncalls?schedule_ids[]=$SCHEDULE_ID&time_zone=UTC" \
  -H "Authorization: Token token=$PD_API_TOKEN" \
  | jq '.oncalls[] | {user: .user.summary, start: .start, end: .end}'

# Who is on call for a specific escalation policy?
curl "https://api.pagerduty.com/oncalls?escalation_policy_ids[]=$POLICY_ID" \
  -H "Authorization: Token token=$PD_API_TOKEN" \
  | jq '.oncalls[] | {level: .escalation_level, user: .user.summary}'
```
