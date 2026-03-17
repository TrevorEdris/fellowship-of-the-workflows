# incident.io — Automation Workflows Reference

Workflows automate repetitive incident response steps. They are triggered by incident lifecycle events and execute a sequence of actions.

---

## Workflow Anatomy

```
trigger:   The event that starts the workflow
condition: Optional filter (only run if incident matches criteria)
steps:     Ordered list of actions to execute
```

---

## Available Triggers

| Trigger | When It Fires |
|---|---|
| `incident.declared` | An incident is created |
| `incident.status_updated` | Status changes (Triage → Active → Resolved) |
| `incident.severity_updated` | Severity changed |
| `incident.updated` | Any field on the incident is updated |
| `incident.resolved` | Incident moves to Resolved status |
| `incident.closed` | Incident is closed (post-resolved) |
| `manual` | Triggered by a user action from Slack or the web UI |
| `alert.fired` | An alert from a connected alert source fires |
| `schedule` | Time-based trigger (e.g., every Monday 09:00) |

---

## Available Actions (Step Types)

| Action | What It Does |
|---|---|
| `incident.create_slack_channel` | Create a dedicated Slack channel for the incident |
| `incident.assign_role` | Assign a role (lead, comms, SME) to a user or on-call engineer |
| `incident.update_status` | Change incident status programmatically |
| `incident.add_timeline_item` | Add a timestamped event to the incident timeline |
| `incident.post_announcement` | Post a Slack message to a specified channel |
| `incident.pin_to_channel` | Pin the incident message in a Slack channel |
| `incident.create_follow_up` | Create a follow-up action item on the incident |
| `incident.set_custom_field` | Set a custom field value |
| `pagerduty.trigger` | Trigger a PagerDuty incident (for hybrid setups) |
| `statuspage.create_incident` | Create or update a status page incident |
| `jira.create_issue` | Create a Jira issue linked to the incident |
| `linear.create_issue` | Create a Linear issue linked to the incident |
| `github.create_issue` | Create a GitHub issue |
| `webhook.post` | POST JSON to an arbitrary webhook endpoint |

---

## Common Workflow Patterns

### 1. Incident Kickoff (Recommended Starting Workflow)

Triggered on every incident declaration:

```
trigger: incident.declared
steps:
  1. Create a Slack channel named #inc-{id}-{title-slug}
  2. Post kickoff message to the channel:
     "Incident declared: {severity} — {title}
      Runbook: {catalog:service.runbook_url}
      Lead: {role:lead or 'Unassigned'}
      Bridge: {incident.slack_channel_link}"
  3. Assign incident lead from primary on-call schedule (if no lead assigned)
  4. Pin the incident message in the channel
```

### 2. Status Update Announcements

Post to a company-wide #incidents channel on status changes:

```
trigger: incident.status_updated
condition: severity IN [critical, high]
steps:
  1. Post to #incidents-updates:
     "{severity} incident: {title}
      Status: {status} (changed from {previous_status})
      Owner: {role:lead}
      More: {incident.url}"
```

### 3. Auto-Escalate Stale Incidents

For incidents open > 30 minutes without a status update:

```
trigger: schedule (every 5 minutes)
condition:
  - incident.status = active
  - incident.created_at < 30 minutes ago
  - incident.last_updated < 15 minutes ago
steps:
  1. Post reminder to incident Slack channel:
     "This incident has been open for {duration} without an update.
      @{role:lead}: Please post a status update or escalate if you need help."
  2. If incident.created_at > 30 minutes AND no lead assigned:
     Assign lead from secondary on-call schedule
```

### 4. Postmortem Creation

Automatically create a postmortem document when an incident is resolved:

```
trigger: incident.resolved
condition: severity IN [critical, high]
steps:
  1. Create follow-up action item: "Schedule postmortem meeting"
     Assigned to: {role:lead}
     Due date: {resolved_at + 2 days}
  2. Post to incident Slack channel:
     "Incident resolved. Postmortem required within 48h (SEV0) or 1 week (SEV1).
      Postmortem template: {link}
      Action item created and assigned to @{role:lead}"
  3. Create Jira ticket for postmortem (if Jira connected):
     Type: Task
     Summary: "Postmortem: {incident.title}"
     Description: {incident.url}
     Assignee: {role:lead}
```

### 5. Status Page Synchronization

Keep your status page in sync with incident status:

```
trigger: incident.status_updated
condition: incident has "customer_facing" label
steps:
  - When status → active:
    statuspage.create_incident(
      title="{incident.title}",
      status="investigating",
      components=[catalog:service.statuspage_component_id]
    )
  - When status → resolved:
    statuspage.update_incident(
      status="resolved",
      message="Service has been restored."
    )
```

### 6. Security Incident Isolation

For incidents of type "Security Incident":

```
trigger: incident.declared
condition: incident_type = "Security Incident"
steps:
  1. Create private Slack channel (not public)
  2. Assign roles: lead = security team on-call, comms = CISO
  3. Post to #security-incidents only (not #incidents-updates)
  4. Set custom field "Requires legal review" = true
  5. Webhook to security incident management system
```

---

## Workflow Conditions

| Condition Field | Operators | Example |
|---|---|---|
| `severity` | `IN`, `NOT IN`, `=`, `!=` | `severity IN [critical, high]` |
| `incident_type` | `=`, `!=` | `incident_type = "Service Outage"` |
| `status` | `=`, `!=` | `status = active` |
| `custom_field.{name}` | `=`, `!=`, `EXISTS` | `custom_field.customer_facing = true` |
| `label` | `HAS` | `label HAS "pci-scope"` |
| `role.{name}` | `ASSIGNED`, `NOT_ASSIGNED` | `role.lead NOT_ASSIGNED` |

---

## Workflow Testing

Test workflows without creating real incidents:

1. Navigate to: **Workflows → [Workflow Name] → Test**
2. Select a recent incident to use as test data
3. Preview the steps that would execute (dry run)
4. Confirm before live execution

Always test new workflows on a non-production incident or a test incident before enabling in production.
