#!/bin/bash
# Usage: git-summary.sh <author> <since> <until> [repo-path]
# Generates a summary of commits by the specified author in the date range
#
# Example: git-summary.sh "trevor@company.com" "2026-01-01" "2026-01-31"
set -e

AUTHOR="$1"
SINCE="$2"
UNTIL="$3"
REPO_PATH="${4:-.}"

if [ -z "$AUTHOR" ] || [ -z "$SINCE" ] || [ -z "$UNTIL" ]; then
  echo "Usage: git-summary.sh <author> <since> <until> [repo-path]"
  echo "Example: git-summary.sh 'trevor@company.com' '2026-01-01' '2026-01-31'"
  exit 1
fi

cd "$REPO_PATH"

echo "=== Git Summary ==="
echo "Author: $AUTHOR"
echo "Period: $SINCE to $UNTIL"
echo "Repository: $(basename $(git rev-parse --show-toplevel))"
echo ""

echo "=== Commit Count ==="
COMMIT_COUNT=$(git log --author="$AUTHOR" --since="$SINCE" --until="$UNTIL" --oneline | wc -l | tr -d ' ')
echo "Total commits: $COMMIT_COUNT"
echo ""

echo "=== Commits by Date ==="
git log --author="$AUTHOR" --since="$SINCE" --until="$UNTIL" \
  --pretty=format:"%ad|%h|%s" --date=short | sort

echo ""
echo ""
echo "=== Files Changed Summary ==="
git log --author="$AUTHOR" --since="$SINCE" --until="$UNTIL" \
  --pretty=format: --name-only | sort | uniq -c | sort -rn | head -20

echo ""
echo ""
echo "=== Insertions/Deletions ==="
git log --author="$AUTHOR" --since="$SINCE" --until="$UNTIL" \
  --pretty=format: --shortstat | grep -v '^$' | awk '
  BEGIN { ins=0; del=0; files=0 }
  {
    for (i=1; i<=NF; i++) {
      if ($i == "insertions(+)" || $i == "insertion(+)") ins += $(i-1)
      if ($i == "deletions(-)" || $i == "deletion(-)") del += $(i-1)
      if ($i == "changed" || $i == "file") files += $(i-1)
    }
  }
  END { print "Files changed: " files; print "Insertions: " ins; print "Deletions: " del }
'
