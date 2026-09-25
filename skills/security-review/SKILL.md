---
name: security-review
description: Use when reviewing code, a diff, or a service specifically for security weaknesses — injection, authn/authz and object-level access (IDOR), SSRF, CSRF, XSS, deserialization, mass assignment, path traversal, secrets, crypto and password storage, sensitive data in logs, dependency risk, rate limiting, headers/CORS — with fixes and regression tests. Not for general bugs (use `code-review`), PR merge readiness (`pr-review`), a scored multi-dimension audit (`code-audit`), or general C#/.NET review (`dotnet-code-review`).
---

# Security Review

Find where untrusted data reaches something that matters, prove each weakness safely, and hand back a fix plus a test that keeps it fixed. Read-only — to apply fixes afterwards, switch to `refactor` (or `dotnet-code-refactor` for C#).

## Ground rules

1. **Defensive and conceptual.** Describe each weakness by root cause, location, impact, fix, and test. No exploit payloads, attack strings, token-forgery or bypass steps — the fix and the regression test carry the proof.
2. **Confirm safely.** Run code only locally or in a test environment the user controls, with the project's own test framework. Never probe production or third-party systems.
3. **Follow the project's stack.** Prefer the framework's built-in control (ORM binding, template auto-escaping, auth middleware, existing rate limiter) over new libraries or hand-rolled code.
4. **Don't guess missing context.** If unseen callers, middleware, or deployment (gateway, WAF) decide severity, say which way it goes and ask — as a Question, or up front (use AskUserQuestion if available, otherwise ask in plain text).
5. **Never repeat a secret.** Refer to exposed credentials by location only.

## Severity

Severity is the impact if the weakness is triggered on a reachable path.

| Tag | Meaning | Typical examples |
|---|---|---|
| 🔴 **BLOCKER** | Security hole, data loss/corruption, crash on reachable input, or broken contract. Must fix before merge/release. | Injection, missing authz/IDOR, privilege escalation, secret in code, untrusted deserialization, SSRF |
| 🟠 **MAJOR** | Real weakness or missing validation at a trust boundary that will bite soon. | Weak password hashing, secrets/PII in logs or responses, no CSRF on cookie-auth writes, credentialed CORS to any origin |
| 🟡 **MINOR** | Hardening or robustness gap worth fixing. | Stack traces to clients, no session expiry, missing security headers |
| 💭 **NIT** | Taste/hygiene. One line. | Framework banner header |

**Exploitability** is a separate note per finding: **High** (anonymous or any logged-in user), **Medium** (needs a role, user interaction, or unusual config), **Low** (needs insider access or another weakness first). Drop one severity level only when you can state the precondition that keeps untrusted actors off the path.

## Workflow

### 1. Map trust boundaries and data flows
- List entry points (routes, message consumers, CLI args, uploads, webhooks, jobs reading external data), their untrusted inputs (params, body, headers, cookies, filenames, URLs, values another service wrote), and the sinks they reach (SQL, shell, templates/HTML, file system, outbound HTTP, deserializers, logs, responses).
- Note the controls in place (authentication, authorization, validation, encoding) and the assets at stake (credentials, PII, money, other tenants' data).

### 2. Checklist sweep
Walk every checklist row against the map. Clean rows go under **Checked OK** with a reason; rows you could not assess go under **Not assessed**.

### 3. Confirm each candidate safely
- **By reading:** trace the value from entry to sink (`file:line`) through middleware, helpers, and ORM calls. A dangerous-looking call that no untrusted input reaches is not a finding (at most a MINOR hardening note).
- **By test (preferred for BLOCKER/MAJOR):** a regression test in the project's framework that fails on the current code and passes after the fix. Shapes that need no attack strings: user B requests user A's resource → 404; a benign value with a quote (`O'Brien`) → normal results, not a 500; a privileged body field → ignored; responses and logs never contain the password or its hash.
- Tag confirmed findings `[verified]`; move what you cannot substantiate to **Questions**.

### 4. Rank and report
Merge findings with one root cause (list every location). Order by severity, then exploitability, then blast radius, and renumber in that order. Each BLOCKER/MAJOR gets a minimal fix snippet and a regression test; a MINOR may have a one-line fix. **Verdict:** REQUEST CHANGES if any BLOCKER or MAJOR; APPROVE WITH COMMENTS if MINORs only; APPROVE if NITs or nothing.

## Checklist

| Area | Look for | Fix direction |
|---|---|---|
| **Injection — SQL/NoSQL** | Request data concatenated into queries, incl. ORM raw-query escape hatches; user-chosen column/sort names | Placeholders/bound parameters; allowlist identifiers (they cannot be bound) |
| **Injection — command** | Shell invocation built from input (`exec`, `system`, `shell=True`) | Argument-array APIs without a shell (`execFile`, `subprocess.run([...])`); allowlist values |
| **Injection — template** | User input used as template *source* rather than template *data* | Never compile user strings as templates; pass them as variables |
| **Authentication** | Non-public routes without auth middleware; tokens not from a CSPRNG, never expiring, or not revoked on logout/password change; JWT decoded without verifying signature and algorithm; reusable reset tokens | Central auth middleware, deny by default; expiring, revocable sessions; verify signature, `exp`, `aud`/`iss` with a fixed algorithm |
| **Authorization / IDOR** | Role checks only in the UI; reads/writes by client-supplied ID not scoped to caller or tenant | Server-side role checks; scope every query (`WHERE id = ? AND owner_id = ?`); return 404 for others' objects |
| **Mass assignment** | Body spread into insert/update/model (`Object.assign(user, req.body)`, `Model(**data)`, `create(req.body)`) | Explicit allowlist or input DTO; set privileged fields (role, owner, price, status) server-side |
| **SSRF** | Server fetches a user-supplied URL (webhooks, previews, import-by-URL) | Allowlist schemes/hosts; block private, loopback, link-local and metadata IPs after resolution; re-check redirects; egress rules |
| **CSRF** | Cookie-authenticated state changes without token or origin check; state changes on GET | `SameSite` cookies plus framework CSRF tokens or Origin checks; no writes on GET |
| **XSS** | Untrusted data rendered raw (`innerHTML`, `dangerouslySetInnerHTML`, `v-html`, the Jinja `safe` filter, string-built HTML) | Auto-escaping templates, `textContent`; sanitize rich text with a maintained sanitizer; CSP as a second layer |
| **Insecure deserialization** | Native object deserializers on untrusted data (`pickle`, Java `ObjectInputStream`, PHP `unserialize`, .NET `BinaryFormatter`, full YAML loaders) | JSON plus schema validation; safe loaders (`yaml.safe_load`) |
| **Path traversal** | File paths built from input (downloads, upload names, archive extraction) | Map IDs to server-side names, or resolve the path and check it stays under the base directory |
| **Secrets** | Keys/passwords in code, committed config, client bundles, error messages | Secret manager or environment, fail fast if missing; rotate anything ever committed (history keeps it) |
| **Crypto & passwords** | Plain or fast hashes (MD5/SHA-*) for passwords; `Math.random`/`random` for tokens; non-constant-time secret comparison; custom crypto; TLS verification disabled | argon2id/scrypt/bcrypt with per-user salt; CSPRNG; constant-time compare; authenticated encryption (e.g., AES-GCM) from a vetted library |
| **Sensitive data in logs/responses** | Request bodies logged wholesale; `SELECT *` or whole ORM objects returned; stack traces sent to clients | Log an allowlist of fields; explicit response DTOs; generic error bodies, details only server-side |
| **Dependency risk** | Known-vulnerable versions, no lock file, abandoned or look-alike packages | Run the ecosystem's audit (`npm audit`, `pip-audit`, `osv-scanner`, `dotnet list package --vulnerable`), else Not assessed |
| **Rate limiting / brute force** | Login, OTP, password reset, signup, expensive endpoints unlimited; no body size limit | Per-account and per-IP limits with backoff (existing limiter or gateway); request size limits |
| **Headers / CORS** | Origin reflected with credentials; missing CSP, HSTS, `X-Content-Type-Options`, frame protection; cookies without `HttpOnly`/`Secure`/`SameSite` | Explicit origin allowlist; headers set centrally; correct cookie flags |

## Output format

A worked example is in `examples/example.txt` (if installed). `template.md` mirrors this format.

````markdown
# Security Review — [component / files / change]

**Scope:** [files and entry points reviewed]
**Findings:** 🔴 [n] · 🟠 [n] · 🟡 [n] · 💭 [n]
**Verdict:** [REQUEST CHANGES / APPROVE WITH COMMENTS / APPROVE]

## Summary
[2–4 sentences: what the code does, the most serious weakness, why this verdict.]

## Trust boundaries and data flows
| Entry point | Untrusted input | Reaches (sink / asset) | Controls present |
|---|---|---|---|
| [route / consumer] | [fields] | [SQL, response, log, …] | [auth, validation, none] |

## Findings

### 🔴 BLOCKER
#### [B1] [Short title] [verified]
**Location:** `path/file.ext:L10-L12`
**Weakness:** [class, optional CWE ID]
**Root cause:** [what the code does wrong, source → sink]
**Impact:** [what an untrusted actor could read, change, or break]
**Exploitability:** [High / Medium / Low — who can trigger it, preconditions]
**Fix:**
```[lang]
[minimal snippet]
```
**Regression test:** [test name — what it asserts]

### 🟠 MAJOR
[Same fields, IDs M1, M2…]

### 🟡 MINOR
[Same fields; Fix may be one line; Regression test optional. IDs m1, m2…]

### 💭 NIT
- `path/file.ext:L5` — [one line]

## Regression tests
```[lang]
[runnable tests in the project's framework, one per BLOCKER/MAJOR where feasible]
```

## Questions
- [Question, and which finding or severity it could change]

## Checked OK
- [Checklist area]: [why it's fine]

## Not assessed
- [Checklist area]: [what was missing to assess it]

## What's good
- [Specific control worth keeping]
````

Omit a severity section with no findings; write "None" under the other sections if empty.

## Special situations
- **Snippet without callers or middleware:** state the dependency ("BLOCKER if this route is not behind the admin guard").
- **Large codebase:** map all entry points, then go deep on auth, money and data-export paths first.
- **One area only** (e.g., "just check auth"): do that area plus secrets; list the rest under Not assessed.
