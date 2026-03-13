#!/bin/bash
# Usage: extract-tickets.sh <author> <since> <until> [repo-path]
# Extracts Jira ticket IDs from commit messages for the specified author and date range
#
# Example: extract-tickets.sh "trevor@company.com" "2026-01-01" "2026-01-31"
set -e

AUTHOR="$1"
SINCE="$2"
UNTIL="$3"
REPO_PATH="${4:-.}"

if [ -z "$AUTHOR" ] || [ -z "$SINCE" ] || [ -z "$UNTIL" ]; then
  echo "Usage: extract-tickets.sh <author> <since> <until> [repo-path]"
  echo "Example: extract-tickets.sh 'trevor@company.com' '2026-01-01' '2026-01-31'"
  exit 1
fi

cd "$REPO_PATH"

# Get all commit messages in the date range for the author
TICKETS=$(git log --author="$AUTHOR" --since="$SINCE" --until="$UNTIL" \
  --pretty=format:"%s %b" | grep -oE '[A-Z]+-[0-9]+' | sort | uniq -c | sort -rn)

if [ -z "$TICKETS" ]; then
  echo "No Jira ticket IDs found in commits."
  exit 0
fi

echo "=== Jira Tickets Referenced ==="
echo "Author: $AUTHOR"
echo "Period: $SINCE to $UNTIL"
echo ""
echo "Count | Ticket ID"
echo "------|----------"
echo "$TICKETS"
