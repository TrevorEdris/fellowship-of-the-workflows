<!--
OUTPUT INSTRUCTIONS:
- Omit any section with nothing meaningful to report
- One sentence per insight, no filler
- Tables for data, bullets for insights
- If a section would just say "none" or "no issues", delete it entirely
-->

# Work Review: {{author}}

**Period:** {{since}} to {{until}}

| Commits | Tickets | Repos |
|---------|---------|-------|
| {{commit_count}} | {{ticket_count}} | {{repo_count}} |

---

## Work by Epic

{{#each epics}}
### {{this.name}}
{{this.description}}

| Ticket | Title | Type | Status |
|--------|-------|------|--------|
{{#each this.tickets}}
| {{this.id}} | {{this.title}} | {{this.type}} | {{this.status}} |
{{/each}}

{{/each}}

{{#if tickets_without_epic}}
### Tickets Without Epic

| Ticket | Title | Type | Status |
|--------|-------|------|--------|
{{#each tickets_without_epic}}
| {{this.id}} | {{this.title}} | {{this.type}} | {{this.status}} |
{{/each}}
{{/if}}

{{#if tickets_without_details}}
### Tickets (Details Unavailable)

The following ticket IDs were referenced but details could not be fetched:
{{#each tickets_without_details}}
- {{this}}
{{/each}}
{{/if}}

---

## Breakdown

**By Type:** {{feature_count}} features, {{bugfix_count}} bugs, {{techdebt_count}} tech debt

{{#if highlights}}
**Highlights:** {{#each highlights}}{{this}}{{#unless @last}}; {{/unless}}{{/each}}
{{/if}}

---

<!-- OMIT this section if no notable trends -->
## Trends

{{#each trends}}
- {{this}}
{{/each}}

---

<!-- OMIT this section if no PRs with 3+ rounds or no concerning patterns -->
## PR Review Concerns

{{#if multi_round_prs}}
| PR | Rounds | Feedback Theme |
|----|--------|----------------|
{{#each multi_round_prs}}
| #{{this.number}} | {{this.rounds}} | {{this.feedback_theme}} |
{{/each}}
{{/if}}

{{#if common_feedback}}
**Recurring feedback:** {{#each common_feedback}}{{this.category}} ({{this.frequency}}x){{#unless @last}}, {{/unless}}{{/each}}
{{/if}}

---

<!-- OMIT this section if nothing notable -->
## Observations

{{#each observations}}
- {{this}}
{{/each}}

<!-- OMIT if all commits have tickets -->
{{#if commits_without_tickets}}
---

## Unlinked Commits

| Date | Hash | Message |
|------|------|---------|
{{#each commits_without_tickets}}
| {{this.date}} | {{this.hash}} | {{this.message}} |
{{/each}}
{{/if}}

---

<!-- OMIT this entire section if no actionable recommendations -->
## Recommendations

{{#each recommendations}}
- {{this}}
{{/each}}

---

<!-- Keep status section minimal, one line -->
**Status:** {{#if mcp_connected}}Jira ✓{{else}}Jira ✗{{/if}} | {{#if gh_connected}}GitHub ✓{{else}}GitHub ✗{{/if}}
