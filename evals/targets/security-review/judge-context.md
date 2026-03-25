# Security Review Judge Context

## Ground Truth Per Prompt

### Prompt 01 (sqli-and-xss): Classic web vulns

**REAL VULNERABILITIES:**
- SQL injection via string formatting in `get_user()` — exploitable by `' OR 1=1 --`
- Reflected XSS in `search()` — user input rendered directly in HTML response
- Hardcoded secret key for JWT signing

**NOT VULNERABILITIES (must not flag):**
- Using `hashlib.sha256` is fine for non-password hashing (it's hashing a cache key)
- The `debug=False` in production config is correct

### Prompt 02 (ssrf): Server-side request forgery

**REAL VULNERABILITIES:**
- SSRF via user-controlled URL in `fetch_preview()` — no validation, can hit internal services
- Missing URL scheme validation (allows `file://`, `gopher://`)

**NOT VULNERABILITIES:**
- The `requests.get` timeout is set correctly
- The error handling returns a generic error (no information leak)

### Prompt 03 (secure-code): No vulnerabilities

**This code is secure.** The review must NOT invent vulnerabilities.
- Parameterized queries used correctly
- Input validation present
- Proper error handling
- Auth middleware applied

A false positive here is a direct failure of the false_positive_rate criterion.

### Prompt 04 (path-traversal): File handling vulns

**REAL VULNERABILITIES:**
- Path traversal in `download_file()` — user controls filename, no sanitization, can read `../../etc/passwd`
- Insecure temporary file creation (predictable name in `/tmp/`)

**NOT VULNERABILITIES:**
- The `os.path.join` in `upload_file()` looks suspicious but the path is validated against an allowlist before use
