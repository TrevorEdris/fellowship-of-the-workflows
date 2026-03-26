# Code Review Judge Context

## Ground Truth Per Prompt

### Prompt 01 (sql-injection-pr): Auth endpoint with SQL injection

**REAL ISSUES (review must find):**
- `auth_service.py:18` — SQL injection via f-string in query: `f"SELECT * FROM users WHERE email = '{email}'"`
- Missing input validation on email parameter (no format check)
- Password comparison using `==` instead of constant-time comparison

**RED HERRINGS (review must NOT flag):**
- `import hashlib` at top — looks suspicious but the function actually uses `hashlib.sha256`, not MD5
- The `async` keyword usage is correct despite looking unusual in this context

**Expected severity:**
- SQL injection → CRITICAL
- Missing input validation → HIGH
- Non-constant-time password comparison → HIGH

### Prompt 02 (clean-refactor): Well-done Go refactor

**REAL ISSUES:** None. The code is correct and well-structured.

**The review should:**
- Acknowledge the refactor is sound
- Optionally note style preferences (not bugs)
- NOT invent issues that don't exist
- Flag the vague PR description as a process concern (not a code issue)

### Prompt 03 (react-xss): Frontend PR with XSS

**REAL ISSUES (review must find):**
- `UserProfile.tsx:24` — XSS via `dangerouslySetInnerHTML` with user-supplied bio
- `CommentList.tsx:15` — Missing `key` prop on list items

**RED HERRINGS (review must NOT flag):**
- Inline style object that computes dynamic values — this is correct, not a "should be CSS" situation

**Expected severity:**
- XSS → CRITICAL
- Missing key prop → MEDIUM

### Prompt 04 (dangerous-migration): DB migration + API changes

**REAL ISSUES (review must find):**
- Migration: `ALTER TABLE users ADD COLUMN phone VARCHAR(20)` without `NOT NULL DEFAULT` — will break existing rows
- API docs: New `/users/:id/phone` endpoint parameters are undocumented

**The Python service code is clean — review should NOT flag issues in it.**

**Expected severity:**
- Dangerous migration → CRITICAL
- Incomplete docs → MEDIUM
