#!/usr/bin/env bash
# Count TODO/FIXME/HACK comments and identify hotspot files
set -euo pipefail

echo "=== Technical Debt Snapshot ==="
echo ""

# Total counts
todo_count=$(grep -rn "TODO\|FIXME\|HACK\|XXX\|WORKAROUND" --include="*.py" --include="*.ts" --include="*.tsx" --include="*.js" --include="*.jsx" --include="*.go" --include="*.rs" --include="*.java" --include="*.rb" . 2>/dev/null | grep -v node_modules | grep -v vendor | grep -v .venv | wc -l | tr -d ' ')

echo "Total debt markers: ${todo_count}"
echo ""

# Breakdown by type
echo "By type:"
for marker in TODO FIXME HACK XXX WORKAROUND; do
    count=$(grep -rn "${marker}" --include="*.py" --include="*.ts" --include="*.tsx" --include="*.js" --include="*.jsx" --include="*.go" --include="*.rs" --include="*.java" --include="*.rb" . 2>/dev/null | grep -v node_modules | grep -v vendor | grep -v .venv | wc -l | tr -d ' ')
    if [ "$count" -gt 0 ]; then
        echo "  ${marker}: ${count}"
    fi
done

echo ""
echo "Top 10 files by debt markers:"
grep -rn "TODO\|FIXME\|HACK\|XXX\|WORKAROUND" --include="*.py" --include="*.ts" --include="*.tsx" --include="*.js" --include="*.jsx" --include="*.go" --include="*.rs" --include="*.java" --include="*.rb" . 2>/dev/null | grep -v node_modules | grep -v vendor | grep -v .venv | cut -d: -f1 | sort | uniq -c | sort -rn | head -10

echo ""
# Lines of code (rough)
loc=$(find . -name "*.py" -o -name "*.ts" -o -name "*.tsx" -o -name "*.js" -o -name "*.go" -o -name "*.rs" -o -name "*.java" -o -name "*.rb" 2>/dev/null | grep -v node_modules | grep -v vendor | grep -v .venv | xargs wc -l 2>/dev/null | tail -1 | awk '{print $1}')
echo "Approximate LOC: ${loc}"
if [ "$loc" -gt 0 ] 2>/dev/null; then
    density=$(echo "scale=2; $todo_count * 1000 / $loc" | bc 2>/dev/null || echo "?")
    echo "Debt density: ${density} markers per 1K LOC"
fi
