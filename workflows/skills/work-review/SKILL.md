---
name: work-review
description: Review work accomplished over a time period by correlating Jira tickets with git commits. Use for self-reviews, peer reviews, sprint retrospectives, or performance discussions.
---

# Work Review

Review and summarize work accomplished over a specified time period by correlating Jira tickets with git commit history.

## When to Use

- Self-review before performance discussions
- Peer review of a colleague's contributions
- Sprint retrospectives
- Preparing status updates or reports

## Prerequisites

### Atlassian MCP (Recommended)

For full functionality, configure Atlassian MCP with browser-based OAuth:

1. Add to `~/.cursor/mcp.json`:
   ```json
   {
     "mcpServers": {
       "atlassian": {
         "url": "https://mcp.atlassian.com/v1/mcp",
         "headers": {}
       }
     }
   }
   ```

2. Restart Cursor
3. On first use, authenticate via browser

### Git Access

Ensure you have access to the repositories you want to analyze.

## Usage

Provide the following information:
- **Author:** Git author name or email
- **Time period:** Start and end dates (e.g., "2026-01-01 to 2026-01-31")
- **Repositories:** Which repos to analyze (optional, defaults to current)

Example prompts:
- "Review my work for the last 2 weeks"
- "Summarize trevor@company.com's commits from Jan 1 to Jan 31"
- "What did the team accomplish in Sprint 47?"

## Review Process

### Step 1: Parse Time Period

Split the requested date range into 2-week chunks to avoid API rate limits:
```bash
python scripts/date-chunks.py 2026-01-01 2026-01-31
```

### Step 2: Gather Git History

For each repository:
```bash
scripts/git-summary.sh "<author>" "<start-date>" "<end-date>"
```

### Step 3: Extract Ticket References

```bash
scripts/extract-tickets.sh "<author>" "<start-date>" "<end-date>"
```

### Step 4: Fetch Jira Details (if MCP available)

For each 2-week chunk:
1. Query Jira for tickets updated in that period
2. Match with extracted ticket IDs from commits
3. Collect ticket details (title, type, status)

**If Atlassian MCP is NOT connected:**
```
⚠️ Atlassian MCP Status: Not connected
Proceeding with git-only review. Ticket details will show IDs only.
```

### Step 5: Fetch Epic Information (if MCP available)

For each ticket, query its parent epic (if any):
1. Group tickets under their parent epics
2. Identify tickets not linked to any epic
3. This enables "work by initiative" view

### Step 6: Analyze PR Review Patterns (via GitHub)

For PRs associated with commits:
```bash
gh pr list --author "<author>" --state merged --search "merged:>YYYY-MM-DD"
```

For each PR, check review history:
- Number of review rounds (approvals after changes requested)
- Time from first review to merge
- Reviewers involved

Flag PRs with 3+ review rounds for discussion.

### Step 7: Correlate and Summarize

Match commits to tickets and generate summary report with:
- Tickets grouped by epic
- Trend analysis across work items
- PR review pattern analysis
- Actionable feedback recommendations

## Rate Limiting Strategy

To avoid Jira API limits, the skill automatically:
1. Splits long date ranges into 2-week chunks
2. Fetches tickets for each chunk sequentially
3. Deduplicates tickets appearing in multiple chunks
4. Aggregates results for final report

## Analysis Features

### Epic Grouping

When Jira MCP is available, tickets are grouped by their parent epic:
- Shows work contribution to larger initiatives
- Identifies scattered work (tickets without epics)
- Helps identify focus areas vs context switching

### Trend Analysis

Identify patterns across completed work:
- **Ticket type distribution:** Heavy on bugs vs features vs tech debt
- **Scope patterns:** Many small tickets vs fewer large ones
- **Collaboration patterns:** Solo work vs paired/reviewed work
- **Time distribution:** Work concentrated in certain periods

### PR Review Pattern Analysis

Analyze GitHub PR history to identify:
- **Multi-round reviews:** PRs requiring 3+ approval cycles
- **Common feedback themes:** Recurring review comments
- **Review turnaround:** Time from PR open to merge
- **Reviewer distribution:** Who reviews this person's code

### Actionable Feedback

At the end of the review, generate actionable recommendations:
- Areas where additional review rigor may help
- Suggestions for reducing review cycles
- Knowledge gaps that training could address
- Process improvements based on observed patterns

## Output Principles

**Be extremely concise.** Every sentence must provide actionable or informative value.

### DO:
- Use bullet points over paragraphs
- State facts directly without preamble
- Omit sections with nothing meaningful to report
- Use tables for structured data
- One sentence per insight, max

### DON'T:
- Add filler phrases ("It's worth noting that...", "Interestingly...")
- Restate information already in tables
- Include empty sections with "No issues found" boilerplate
- Pad recommendations to seem thorough
- Explain obvious conclusions

### Examples

**Bad (verbose):**
> "Looking at the PR review patterns, it's interesting to note that there were several instances where multiple rounds of review were required. This suggests that there may be opportunities to improve the initial PR quality before requesting review."

**Good (concise):**
> "3 PRs had 4+ review rounds. Common theme: missing edge case tests."

**Bad (filler):**
> "Overall, the work completed during this period demonstrates a solid contribution to the team's goals. The tickets completed align well with the sprint objectives."

**Good (concise):**
> "12 tickets completed. 80% aligned to Epic: B2B Partner Onboarding."

### Section Omission Rules

- **Omit "Tickets Without Epic"** if all tickets have epics
- **Omit "PR Review Analysis"** if no concerning patterns found
- **Omit "Actionable Feedback"** subsections if no recommendations (don't say "none")
- **Omit "Commits Without Tickets"** if all commits reference tickets

## Output Format

See `assets/review-template.md` for the template structure. Apply Output Principles above — omit empty sections, keep insights to one line each.

## Scripts

### git-summary.sh
```bash
scripts/git-summary.sh "author@email.com" "2026-01-01" "2026-01-31"
```

### extract-tickets.sh
```bash
scripts/extract-tickets.sh "author@email.com" "2026-01-01" "2026-01-31"
```

### date-chunks.py
```bash
python scripts/date-chunks.py 2026-01-01 2026-03-31
# Outputs 2-week chunk boundaries as JSON
```

### correlate.py
```bash
python scripts/correlate.py --author "author@email.com" --since 2026-01-01 --until 2026-01-31
```

## Graceful Degradation

| MCP Status | Behavior |
|------------|----------|
| Connected | Full ticket details (title, type, status, description) |
| Not connected | Ticket IDs only, note displayed to user |
| Partial failure | Available data shown, failures noted |
