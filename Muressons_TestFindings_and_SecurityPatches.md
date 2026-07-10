# Muressons — Test Investigation + Security Patch Drafts (Claude Fable 5)

*Owner-authorised. Patches below are drafts for you to review and apply — nothing in your repo was modified.*

---

## Part A — Test-failure investigation (with an important correction to v2)

I installed the deps and **ran the suite for real** this time (`USE_MEMORY_DB=true DEBUG=true pytest`). Result:

**955 passed, 1 failed.**

### Correction to my v2 report
My v2 claim of "3 failing engine tests (R5/R8)" was **wrong** — it was based on a committed artifact, `backend/pytest_out.txt`, dated **2026-03-27**, while `tests/test_round_logic.py` was updated **2026-06-18**. Running the current tests, **all R5/R8 round-logic tests pass**. The engine and tests do *not* actually disagree. I should have executed the suite before reporting the file's contents as current; apologies for the false alarm.

The finding that survives, in weaker form: **stale, misleading test artifacts are committed.** `pytest_out.txt` (shows failures that no longer exist) and `test_results.txt` (only two login lines) will mislead anyone auditing the project. **Recommendation:** delete both, stop committing test logs, and add a CI job so the *live* result is the source of truth.

### The one genuine failure — and it's a false alarm too, but instructive
`tests/test_security_guards.py::test_path_traversal_sanitisation` fails **on Linux** (your Docker/Railway deploy target). The test asserts that `os.path.basename("..\\..\\admin_router.py")` strips the backslashes — but on Linux `basename` treats `\` as an ordinary character, so it returns the string unchanged and the assert fails. On Windows it would pass. So the **test encodes a false assumption**, not a real vulnerability.

I checked the actual upload endpoint (`admin_router.py:5271`) to be sure, and it is **correctly defended**:

```python
bare_name = os.path.basename(file.filename or "upload")
bare_name = bare_name.replace("..", "").replace("/", "").replace("\\", "").replace("\x00", "")
...
file_path = os.path.realpath(os.path.join(upload_dir, safe_name))
if not file_path.startswith(os.path.realpath(upload_dir)):
    raise HTTPException(status_code=400, detail="Invalid filename.")
```

Explicit `..`/`/`/`\`/null stripping **plus** a realpath containment check — robust on both OSes. **Recommendation:** fix the *test* so it exercises the real sanitiser (`_sanitise_upload_name`) rather than raw `basename`, so CI passes cross-platform and actually guards the real code path. Draft below (Patch 5).

**Net:** engine math is sound and the upload path is safe. The real issues are hygiene (stale artifacts, a flawed test) plus the four security items below, which stand.

---

## Part B — Security patch drafts

> Apply-and-review. Each is minimal, self-contained, and preserves behaviour for legitimate users. Line numbers reference the current tree.

### Patch 1 — 🔴 Remove the hardcoded master-password fallback
**File:** `backend/config.py:30-31`

**Now:**
```python
_mp = os.getenv("MASTER_PASSWORD", "").strip().strip('"').strip("'")
MASTER_PASSWORD: str = _mp if _mp else "sim2026@iim@"
```

**Draft:**
```python
# Break-glass master password. EMPTY = disabled (the only safe default).
# Never hardcode a value here; supply via env only for a recovery window.
MASTER_PASSWORD: str = os.getenv("MASTER_PASSWORD", "").strip().strip('"').strip("'")
```
Every call site already does `bool(MASTER_PASSWORD) and hmac.compare_digest(...)`, so an empty value cleanly disables the bypass — no other code changes needed.

**Also required (outside the file):**
1. Rotate: treat `sim2026@iim@` as compromised.
2. Purge from history: `git filter-repo --replace-text <(echo 'sim2026@iim@==>REDACTED')` (or BFG), then force-push and have collaborators re-clone.
3. Scrub `.env` / `backend/.env` working copies; keep only `.env.example` with a blank value.
4. In `test_all_pathways_x_paradigms.py` / `test_e2e_full_flow.py`, the `os.environ['MASTER_PASSWORD']='321'` lines are fine for local tests but ensure `test_*` are excluded from any shipped zip (they already are in `.dockerignore`? — verify).

---

### Patch 2 — 🔴 Close the empty-password login bypass
**File:** `backend/router.py:286` (and mirror the same fix at the facilitator paths `admin_router.py:1469` if they share the pattern)

**Now:**
```python
stored_pw = player_record.get("password", "")
master_ok = bool(MASTER_PASSWORD) and hmac.compare_digest(req.password, MASTER_PASSWORD)
if stored_pw and not master_ok and not _verify_pw(req.password, stored_pw):
    raise HTTPException(status_code=403, detail="Incorrect password.")
```
The bug: when `stored_pw == ""` the whole `if` is skipped, so **any** password is accepted for pre-generated (`allowed_player_ids`) accounts.

**Draft:**
```python
stored_pw = player_record.get("password", "")
master_ok = bool(MASTER_PASSWORD) and hmac.compare_digest(req.password, MASTER_PASSWORD)

if not master_ok:
    if not stored_pw:
        # Pre-generated player with no password yet: require a first-login set,
        # never silently accept. Force the client into the set-password flow.
        raise HTTPException(
            status_code=status.HTTP_428_PRECONDITION_REQUIRED,
            detail="Password not set. Please set a password to activate this player ID.",
        )
    if not _verify_pw(req.password, stored_pw):
        raise HTTPException(status_code=403, detail="Incorrect password.")

# Auto-upgrade legacy plaintext on success
if stored_pw and not master_ok:
    upgraded = _maybe_upgrade_pw(req.password, stored_pw)
    if upgraded:
        player_record["password"] = upgraded
```
If you prefer not to build a set-password flow now, the minimal safe version is: replace `if stored_pw and not master_ok and not _verify_pw(...)` with `if not master_ok and not _verify_pw(req.password, stored_pw or ""):` — an empty stored password then always fails verification, blocking anonymous entry.

---

### Patch 3 — 🟠 Stop using `session_id` as the player WS bearer token
**File:** `backend/admin_router.py:5675-5686`

**Problem:** `is_player = (token == session_id)` makes the session identifier itself the credential. Anyone who sees a session_id (URL, log, screen-share) can attach.

**Draft (issue a signed, short-lived WS ticket):**
```python
# In auth_jwt.py — add alongside the facilitator token helpers:
def create_player_ws_ticket(session_id: str, player_id: str, ttl_seconds: int = 900) -> str:
    now = datetime.now(timezone.utc)
    payload = {"sid": session_id, "pid": player_id, "typ": "ws",
               "iat": now, "exp": now + timedelta(seconds=ttl_seconds)}
    return _jose_jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)

def verify_player_ws_ticket(token: str, session_id: str) -> bool:
    try:
        p = _jose_jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        return p.get("typ") == "ws" and p.get("sid") == session_id
    except JWTError:
        return False
```
```python
# admin_router.py session_websocket:
is_facilitator = _ws_authenticate_facilitator(websocket, token)
is_player = verify_player_ws_ticket(token or "", session_id)   # was: token == session_id
if not is_facilitator and not is_player:
    await websocket.close(code=4001, reason="Unauthorized")
    return
```
The player fetches a ticket from an authenticated REST call (e.g. add `ws_ticket` to the `player_login` response) and passes it as `?token=`. Short TTL + refresh keeps it cheap. This is the one patch that needs a small frontend change (swap what the WS `?token=` carries).

---

### Patch 4 — 🟠 Sanitise the mailbox HTML render
**File:** `frontend/app/components/ExecutiveMailbox.js:334-338`

**Now:**
```jsx
{expandedMessage.html ? (
    <div
        className={`${styles.modalBody} ${styles.htmlArtifact}`}
        dangerouslySetInnerHTML={{ __html: expandedMessage.body }}
    />
) : ( ... )}
```
Every other HTML render in the app (`RoundBriefing`, `InlineReviewViewer`, `FacilitatorTeleprompter`) already runs through `sanitizeHtml`. This one doesn't.

**Draft:**
```jsx
import { sanitizeHtml } from '@/app/utils/sanitize';  // add at top
...
<div
    className={`${styles.modalBody} ${styles.htmlArtifact}`}
    dangerouslySetInnerHTML={{ __html: sanitizeHtml(expandedMessage.body) }}
/>
```
Zero behaviour change for the current hardcoded/engine-generated messages (they use only the whitelisted tags), but it closes the door if any message body ever originates from a facilitator broadcast, LLM output, or future user input.

---

### Patch 5 — 🟢 Fix the flawed (cross-platform-failing) sanitisation test
**File:** `backend/tests/test_security_guards.py:146-160`

Test the **real** sanitiser, not `os.path.basename` (whose behaviour is OS-dependent):
```python
def test_path_traversal_sanitisation():
    """The real upload sanitiser must strip traversal on any OS."""
    from admin_router import _sanitise_upload_name   # extract the inline logic into this helper
    for name in ["../../etc/passwd", "..\\..\\admin_router.py",
                 "foo/../../../secret.txt", "\x00evil.sh"]:
        safe = _sanitise_upload_name(name)
        assert ".." not in safe and "/" not in safe and "\\" not in safe and "\x00" not in safe
```
This requires a tiny refactor: pull the `bare_name = ...` block from `admin_router.py:5272-5276` into a module-level `_sanitise_upload_name(filename: str) -> str` and call it from both the endpoint and the test. Improves testability and removes the last red test cross-platform.

---

## Part C — Do this in order

1. **Patch 1** (master password) + rotate + history purge — highest urgency, smallest change.
2. **Patch 2** (empty-password bypass) — the minimal one-line variant is safe to ship immediately.
3. **Patch 4** (mailbox sanitise) — one-line, no downside.
4. **Patch 3** (WS ticket) — needs the small paired frontend change; schedule with a frontend deploy.
5. **Patch 5** + delete `pytest_out.txt` / `test_results.txt` + add a CI gate that runs `pytest` on push.

I can write any of these as ready-to-apply diffs against your working tree if you'd like — just say which.
