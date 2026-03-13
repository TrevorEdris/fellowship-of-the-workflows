#!/usr/bin/env python3
"""
Correlates git commits with Jira tickets.

This script is designed to be used by the work-review skill to match
commits to their associated Jira tickets and generate a structured report.

Usage:
    correlate.py --author <author> --since <date> --until <date> [--repo <path>]

The script:
1. Fetches git commits for the specified author and date range
2. Extracts Jira ticket IDs from commit messages
3. Outputs a structured correlation report

Note: Jira ticket details (title, status) are fetched by the agent
using the Atlassian MCP, not by this script. This script provides
the git-side data for correlation.
"""
import subprocess
import re
import json
import argparse
from collections import defaultdict
from datetime import datetime


def get_commits(author: str, since: str, until: str, repo_path: str = ".") -> list:
    """Fetch commits for the specified author and date range."""
    cmd = [
        "git", "-C", repo_path, "log",
        f"--author={author}",
        f"--since={since}",
        f"--until={until}",
        "--pretty=format:%H|%ad|%s",
        "--date=short"
    ]
    
    result = subprocess.run(cmd, capture_output=True, text=True)
    commits = []
    
    for line in result.stdout.strip().split("\n"):
        if not line:
            continue
        parts = line.split("|", 2)
        if len(parts) == 3:
            commits.append({
                "hash": parts[0],
                "date": parts[1],
                "message": parts[2]
            })
    
    return commits


def extract_ticket_ids(message: str) -> list:
    """Extract Jira ticket IDs from a commit message."""
    pattern = r'[A-Z]+-[0-9]+'
    return list(set(re.findall(pattern, message)))


def correlate(commits: list) -> dict:
    """Correlate commits with their ticket IDs."""
    ticket_to_commits = defaultdict(list)
    commits_without_tickets = []
    
    for commit in commits:
        tickets = extract_ticket_ids(commit["message"])
        if tickets:
            for ticket in tickets:
                ticket_to_commits[ticket].append(commit)
        else:
            commits_without_tickets.append(commit)
    
    return {
        "ticket_to_commits": dict(ticket_to_commits),
        "commits_without_tickets": commits_without_tickets,
        "summary": {
            "total_commits": len(commits),
            "tickets_referenced": len(ticket_to_commits),
            "commits_with_tickets": len(commits) - len(commits_without_tickets),
            "commits_without_tickets": len(commits_without_tickets)
        }
    }


def generate_report(correlation: dict, author: str, since: str, until: str) -> str:
    """Generate a human-readable correlation report."""
    lines = [
        "=" * 60,
        "WORK REVIEW - GIT CORRELATION REPORT",
        "=" * 60,
        f"Author: {author}",
        f"Period: {since} to {until}",
        "",
        "SUMMARY",
        "-" * 40,
        f"Total commits: {correlation['summary']['total_commits']}",
        f"Tickets referenced: {correlation['summary']['tickets_referenced']}",
        f"Commits with tickets: {correlation['summary']['commits_with_tickets']}",
        f"Commits without tickets: {correlation['summary']['commits_without_tickets']}",
        "",
        "TICKETS AND COMMITS",
        "-" * 40,
    ]
    
    for ticket, commits in sorted(correlation["ticket_to_commits"].items()):
        lines.append(f"\n{ticket} ({len(commits)} commits)")
        for commit in commits:
            lines.append(f"  {commit['date']} {commit['hash'][:7]} {commit['message'][:60]}")
    
    if correlation["commits_without_tickets"]:
        lines.append("\n\nCOMMITS WITHOUT TICKET REFERENCES")
        lines.append("-" * 40)
        for commit in correlation["commits_without_tickets"]:
            lines.append(f"  {commit['date']} {commit['hash'][:7]} {commit['message'][:60]}")
    
    lines.append("\n" + "=" * 60)
    
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description="Correlate git commits with Jira tickets")
    parser.add_argument("--author", required=True, help="Git author name or email")
    parser.add_argument("--since", required=True, help="Start date (YYYY-MM-DD)")
    parser.add_argument("--until", required=True, help="End date (YYYY-MM-DD)")
    parser.add_argument("--repo", default=".", help="Repository path (default: current)")
    parser.add_argument("--json", action="store_true", help="Output as JSON")
    
    args = parser.parse_args()
    
    commits = get_commits(args.author, args.since, args.until, args.repo)
    correlation = correlate(commits)
    
    if args.json:
        output = {
            "author": args.author,
            "since": args.since,
            "until": args.until,
            "correlation": correlation
        }
        print(json.dumps(output, indent=2))
    else:
        print(generate_report(correlation, args.author, args.since, args.until))


if __name__ == "__main__":
    main()
