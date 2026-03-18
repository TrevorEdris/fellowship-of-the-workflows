#!/usr/bin/env bash
# Fetch PRs merged per week for the last N weeks using gh api
set -euo pipefail

WEEKS=${1:-8}

echo "Week | PRs Merged"
echo "-----|----------"

for i in $(seq 0 $((WEEKS - 1))); do
    start=$(date -v-"$((i + 1))"w +%Y-%m-%dT00:00:00Z 2>/dev/null || date -d "$((i + 1)) weeks ago" +%Y-%m-%dT00:00:00Z)
    end=$(date -v-"${i}"w +%Y-%m-%dT00:00:00Z 2>/dev/null || date -d "${i} weeks ago" +%Y-%m-%dT00:00:00Z)

    count=$(gh api graphql -f query="
        query {
            search(query: \"repo:{owner}/{repo} is:pr is:merged merged:${start}..${end}\", type: ISSUE) {
                issueCount
            }
        }
    " --jq '.data.search.issueCount' 2>/dev/null || echo "?")

    week_label=$(date -v-"${i}"w +%m/%d 2>/dev/null || date -d "${i} weeks ago" +%m/%d)
    echo "${week_label} | ${count}"
done
