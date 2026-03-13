---
name: git-workflow
description: "Interactive git workflow assistant. Generates conventional commits, PR descriptions, enforces branch naming, guides merge conflict resolution, manages worktrees, and handles branch completion. Triggered by: commit, PR, branch, merge conflict, worktree, finish branch, conventional commit, squash, rebase."
user-invocable: true
argument-hint: "[commit|pr|branch|conflict|worktree|finish]"
---

# Git Workflow Assistant

Active workflow assistance for common git operations. Branch protection and credential safety are handled by the git-safety rule. This skill focuses on generating correct output: well-formed commits, complete PR descriptions, valid branch names, and guided conflict resolution.

---

## Context

CURRENT BRANCH:
```
!`git branch --show-current`
```

GIT STATUS:
```
!`git status --short`
```

RECENT COMMITS (this branch):
```
!`git log --oneline -10 2>/dev/null`
```

MERGE CONFLICTS:
```
!`git diff --name-only --diff-filter=U 2>/dev/null || echo "None"`
```

---

## Mode Selection

Detect the sub-workflow from the argument or from context. If ambiguous, ask.

| Mode | Trigger | Action |
|------|---------|--------|
| `commit` | Staged changes exist, user wants to commit | Generate conventional commit message |
| `pr` | User wants to open a PR | Generate PR body, push, create PR via `gh` |
| `branch` | User wants a new branch | Enforce naming convention, create branch |
| `conflict` | Conflicts detected in status | Guide per-file resolution |
| `worktree` | User wants isolated workspace | Create worktree with setup |
| `finish` | Work is done, branch ready | Test, then present 4 disposition options |

**Auto-detection rules:**
- Untracked/staged files present + no conflicts → suggest `commit`
- Conflict markers in status (`UU`) → suggest `conflict`
- No argument and clean branch → ask which mode

---

## Sub-Workflow: commit

Generate a conventional commit message from staged changes.

### Steps

1. Check staged changes: `git diff --cached --stat`
2. If nothing staged, show unstaged changes with `git diff --stat` and ask which files to stage
3. Analyze the full diff: `git diff --cached`
4. Determine commit type from the change pattern:
   - New files implementing behavior → `feat`
   - Fixed logic or regression → `fix`
   - Code moved/restructured, behavior unchanged → `refactor`
   - Only test files changed → `test`
   - Only documentation changed → `docs`
   - Build, CI, or dependency changes → `chore`
   - CPU/memory improvements → `perf`
   - Pipeline definition changes → `ci`
5. Determine scope from the primary package, module, or component affected
6. Draft message: `<type>(<scope>): <description>` — imperative, present tense, under 72 chars
7. Present message for approval or editing
8. Commit with the approved message, appending `Co-Authored-By` trailer

### Format

```
<type>(<scope>): <short description>

<optional body — explain WHY, not what>

Co-Authored-By: Claude <noreply@anthropic.com>
```

### References

See `references/conventional-commits.md` for type definitions and scope guidelines.

### Script

`scripts/commit-msg.sh` analyzes the staged diff and outputs a suggested type, scope, and description.

```bash
bash scripts/commit-msg.sh
```

---

## Sub-Workflow: pr

Generate a complete PR description, push the branch, and create the PR.

### Steps

1. Determine base branch — check for `main`, `master`, `develop` in that order
2. Collect commits since divergence: `git log --oneline <base>..HEAD`
3. Collect diff stat: `git diff <base>...HEAD --stat`
4. Generate PR title (under 70 characters) summarizing the overall change
5. Generate PR body using `assets/pr-template.md` structure
6. Check if branch tracks a remote: `git status -sb`
   - If not tracking: `git push -u origin <branch>`
   - If already tracking: `git push`
7. Check for `gh` CLI availability
   - If available: `gh pr create --title "<title>" --body "<body>"`
   - If unavailable: print the title and body to copy manually, plus the push URL
8. Report the PR URL

### Script

`scripts/pr-body.sh` generates the formatted PR body from commit history.

```bash
bash scripts/pr-body.sh [base-branch]
```

### Graceful degradation

If `gh` is not installed, output:
- The full PR body (ready to paste)
- The remote URL for opening a PR manually
- Instructions to install `gh`: `brew install gh` or https://cli.github.com

---

## Sub-Workflow: branch

Create a correctly named branch following team conventions.

### Steps

1. Ask for branch purpose: `feature | fix | chore | docs | refactor | test | hotfix | release`
2. Ask for ticket ID (optional — skip if none)
3. Ask for a short description (2-5 words)
4. Generate branch name:
   - With ticket: `<type>/<ticket>-<kebab-description>`
   - Without ticket: `<type>/<kebab-description>`
5. Validate the generated name with `scripts/branch-check.sh`
6. Show the name, confirm with user
7. Create and switch: `git checkout -b <branch-name>`

### Rules

See `references/branch-naming.md` for full conventions. Key constraints:
- Lowercase only
- Hyphens, not underscores or spaces
- No special characters except `/` and `-`
- Description segment max 50 characters
- Total name max 100 characters

### Script

```bash
bash scripts/branch-check.sh "feature/PROJ-123-add-oauth-login"
```

---

## Sub-Workflow: conflict

Guide through merge conflict resolution file by file.

### Steps

1. List conflicting files: `git diff --name-only --diff-filter=U`
2. For each file:
   a. Show the conflict with context: `git diff <file>`
   b. Identify what branch each side came from (ours = current branch, theirs = incoming)
   c. Classify the conflict type and recommend a resolution strategy:
      - **Lockfile** (`package-lock.json`, `Pipfile.lock`, `go.sum`): Delete the file, regenerate with the package manager — do not hand-edit
      - **Import ordering**: Accept both sets of imports, deduplicate, sort
      - **Adjacent line edits**: Both changes are usually needed — merge manually
      - **Deleted-vs-modified**: Determine which intent wins based on the PR context
      - **Config/schema files**: Review each block; typically accept incoming for additive changes
   d. Assist with the resolution (read the file, propose the resolved content)
   e. Mark resolved: `git add <file>`
3. After all files resolved, verify no markers remain: `git diff --check`
4. Continue the in-progress operation: `git rebase --continue` or `git merge --continue`

### References

See `references/merge-conflict-guide.md` for detailed patterns and strategies.

---

## Sub-Workflow: worktree

Create an isolated workspace for parallel development without disturbing the current branch.

### Steps

1. Determine worktree location (priority order):
   - If `.worktrees/` exists in project root, use `.worktrees/<branch-name>`
   - If `worktrees/` exists in project root, use `worktrees/<branch-name>`
   - Ask user: project-local (`.worktrees/`) vs global (`~/.local/share/worktrees/<project>/`)
2. If creating a new location, verify it is in `.gitignore` — add it if missing
3. Determine the branch:
   - If user specified a branch: use existing or create new
   - Otherwise: run the `branch` sub-workflow to create a properly named branch
4. Create worktree: `git worktree add <path> -b <branch>` (or `git worktree add <path> <branch>` if existing)
5. Auto-detect and run project setup in the worktree directory:
   - `package.json` present → `npm install` (or `pnpm install` / `yarn install`)
   - `Pipfile` or `requirements.txt` → `pip install -r requirements.txt` or `pipenv install`
   - `go.mod` → `go mod download`
   - `Makefile` with `setup` target → `make setup`
   - `Taskfile.yml` with `setup` task → `task setup`
6. Run the project's test suite to verify a clean baseline
7. Report the worktree location and branch

---

## Sub-Workflow: finish

Complete work on a branch and choose its disposition.

### Steps

1. Auto-detect test runner and run tests:
   - `package.json` with `test` script → `npm test`
   - `pytest.ini` or `pyproject.toml` → `pytest`
   - `go.mod` → `go test ./...`
   - `Taskfile.yml` → look for `test` task
   - If no runner detected, ask user for the test command
2. Report test results. If tests fail, stop and surface the failures — do not proceed
3. Determine base branch (`main`, `master`, or `develop`)
4. Show a summary: branch name, commit count, files changed
5. Present exactly 4 options:

   ```
   How do you want to finish this branch?

   1. Merge locally — merge to <base> on this machine now
   2. Open a Pull Request — push and create a PR (delegates to pr sub-workflow)
   3. Keep as-is — leave the branch, do nothing
   4. Discard this work — delete the branch and abandon changes (requires confirmation)
   ```

6. Execute the chosen option:
   - **Option 1**: `git checkout <base> && git merge --no-ff <branch>`
   - **Option 2**: Delegate to `pr` sub-workflow
   - **Option 3**: Report branch status and exit
   - **Option 4**: Prompt user to type `discard` to confirm, then `git branch -D <branch>`
7. If a worktree was involved, offer to remove it: `git worktree remove <path>`

---

## Integration Points

| Skill / Rule | Relationship |
|---|---|
| `git-safety` rule | Passive guard (always on). This skill is the active complement — it generates good behavior, the rule prevents bad behavior. |
| `code-review` skill | The `pr` sub-workflow creates PRs that `code-review` can then review. No direct coupling. |
| `session-handoff` skill | The `finish` sub-workflow's "keep as-is" option pairs naturally with creating a session handoff. |

---

## References

- `references/conventional-commits.md` — Commit type definitions, scope guidelines, breaking change format
- `references/branch-naming.md` — Branch naming conventions and examples
- `references/merge-conflict-guide.md` — Conflict patterns and resolution strategies

## Scripts

- `scripts/commit-msg.sh` — Analyze staged diff, suggest type + scope + description
- `scripts/pr-body.sh` — Generate PR body from commit history and diff stat
- `scripts/branch-check.sh` — Validate branch name, return PASS/FAIL with suggestion

## Assets

- `assets/pr-template.md` — PR body template used by the `pr` sub-workflow
