# Better Stack — Status Pages Reference

Better Stack provides fully branded status pages with custom domains, custom CSS, subscriber management (email and SMS), and automatic incident propagation from monitors.

---

## Status Page Architecture

```
Status Page
├── Sections (logical groupings, e.g., "Core APIs", "Infrastructure")
│   └── Resources (individual components, linked to monitors or monitor groups)
├── Subscribers (email/SMS notification opt-in list)
└── Incident History (automatically populated from monitor incidents)
```

---

## Terraform Configuration

### Basic Status Page

```hcl
resource "betterstack_status_page" "main" {
  company_name    = "Acme Corp"
  company_url     = "https://acme.example.com"
  contact_url     = "https://support.acme.example.com"
  logo_url        = "https://assets.acme.example.com/logo.png"

  # Custom domain — requires DNS CNAME setup
  custom_domain   = "status.acme.example.com"

  # Subscriber opt-in — who can subscribe for notifications
  subscriptions_enabled = true

  # Timezone for incident timestamps shown to subscribers
  timezone        = "America/New_York"
}
```

### Sections

Sections group related components on the status page.

```hcl
resource "betterstack_status_page_section" "core_apis" {
  status_page_id = betterstack_status_page.main.id
  name           = "Core APIs"
  position       = 1
}

resource "betterstack_status_page_section" "infrastructure" {
  status_page_id = betterstack_status_page.main.id
  name           = "Infrastructure"
  position       = 2
}

resource "betterstack_status_page_section" "integrations" {
  status_page_id = betterstack_status_page.main.id
  name           = "Third-Party Integrations"
  position       = 3
}
```

### Resources (Components)

Resources link status page components to Better Stack monitors or monitor groups.

```hcl
# Link a single monitor to a status page section
resource "betterstack_status_page_resource" "order_api" {
  status_page_id         = betterstack_status_page.main.id
  status_page_section_id = betterstack_status_page_section.core_apis.id

  resource_id   = betterstack_monitor.order_service.id
  resource_type = "Monitor"
  public_name   = "Order API"
  position      = 1
}

# Link a monitor group (shows aggregate status)
resource "betterstack_status_page_resource" "platform_services" {
  status_page_id         = betterstack_status_page.main.id
  status_page_section_id = betterstack_status_page_section.core_apis.id

  resource_id   = betterstack_monitor_group.platform.id
  resource_type = "MonitorGroup"
  public_name   = "Platform Services"
  position      = 2
}
```

---

## Custom Domain Setup

To use a custom domain (e.g., `status.acme.example.com`):

1. Set `custom_domain` in `betterstack_status_page`
2. Add a DNS CNAME record pointing to `betterstack.statuspage.io`
3. Better Stack provisions an SSL certificate automatically (may take up to 30 minutes)

```dns
; DNS configuration
status.acme.example.com  CNAME  betterstack.statuspage.io
```

---

## Custom CSS

Style the status page to match your brand. Configure via the Better Stack UI under **Status Pages → [Page] → Design → Custom CSS**.

```css
/* Example: Match company brand colors */
:root {
  --color-primary: #1a56db;
  --color-success: #057a55;
  --color-warning: #c27803;
  --color-danger:  #c81e1e;
}

.status-page-header {
  background-color: #1e1e2e;
  color: #ffffff;
}

.status-badge-operational {
  background-color: var(--color-success);
}
```

---

## Subscriber Management

### Email Subscribers

Subscribers opt in via the status page. They receive:
- Incident created notifications
- Status update notifications (Investigating → Identified → Monitoring → Resolved)
- Resolved notifications

### SMS Subscribers

Available on paid plans. SMS notifications use the same incident lifecycle events.

### Exporting Subscriber List

```bash
curl -X GET \
  "https://uptime.betterstack.com/api/v2/status-pages/STATUS_PAGE_ID/subscribers" \
  -H "Authorization: Bearer ${BETTER_STACK_API_TOKEN}"
```

### Import Subscribers (Bulk)

Useful when migrating from another status page provider (Statuspage.io, etc.):

```bash
curl -X POST \
  "https://uptime.betterstack.com/api/v2/status-pages/STATUS_PAGE_ID/subscribers" \
  -H "Authorization: Bearer ${BETTER_STACK_API_TOKEN}" \
  -H "Content-Type: application/json" \
  -d '{
    "subscribers": [
      {"email": "user@example.com"},
      {"email": "other@example.com"}
    ]
  }'
```

---

## Incident Communication via Status Page

Better Stack automatically creates status page incidents when a linked monitor goes down. Manual control:

### Manual Status Page Incident

Use when a non-monitored issue (e.g., third-party dependency outage) needs communication:

```bash
curl -X POST \
  "https://uptime.betterstack.com/api/v2/status-pages/STATUS_PAGE_ID/status-reports" \
  -H "Authorization: Bearer ${BETTER_STACK_API_TOKEN}" \
  -H "Content-Type: application/json" \
  -d '{
    "status_report_update": {
      "message": "We are investigating reports of elevated error rates in the payment integration. Our engineering team is actively investigating.",
      "affected_resources": [
        {"resource_type": "StatusPageResource", "resource_id": "RESOURCE_ID"}
      ]
    }
  }'
```

### Update Status Page Incident (Add Update)

```bash
curl -X POST \
  "https://uptime.betterstack.com/api/v2/status-pages/STATUS_PAGE_ID/status-reports/REPORT_ID/status-updates" \
  -H "Authorization: Bearer ${BETTER_STACK_API_TOKEN}" \
  -H "Content-Type: application/json" \
  -d '{
    "status_update": {
      "message": "Root cause identified: upstream payment gateway API is experiencing degraded performance. We are in contact with the provider.",
      "status": "identified"
    }
  }'
```

### Incident Status Values

| Status | Meaning | When to Use |
|---|---|---|
| `investigating` | Team is actively investigating | First update; root cause unknown |
| `identified` | Root cause known; fix in progress | After root cause confirmed |
| `monitoring` | Fix applied; watching for recovery | After remediation; before full resolution |
| `resolved` | Service fully restored | Final update |

---

## Migration from Statuspage.io

When migrating from Atlassian Statuspage (Statuspage.io):

1. Export component list from Statuspage.io API
2. Export subscriber list (email addresses)
3. Create equivalent components as `betterstack_status_page_resource` resources
4. Import subscribers via Better Stack API (bulk import endpoint above)
5. Update DNS CNAME from Statuspage.io CDN to `betterstack.statuspage.io`
6. Update any hardcoded `status.yourdomain.com` references in runbooks, on-call notes
7. Notify subscribers via old Statuspage.io with migration announcement before cutting over DNS
