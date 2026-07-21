# Splitting `backend/router.py` into per-feature commits

`router.py` has ~255 uncommitted lines mixing **six** features, some interleaved
inside the same hunk. This is a `git add -p` walkthrough to land them as clean
commits. It only stages `router.py` worktree hunks + companion files — it does
NOT touch your staged god-file decomposition (that lives in the index for other
files).

## The 13 hunks, by feature

| Hunk | Location | Feature | Action |
|---|---|---|---|
| h0 | `class JoinSessionRequest` | join-policy | Commit A (`y`) |
| h1 | `join_session` (+67) | join-policy | Commit A (`y`) |
| h2 | `join_session` (+12) | join-policy | Commit A (`y`) |
| h3 | `get_session_info` (+17) | join-policy | Commit A (`y`) — eyeball |
| h4 | `get_session_info` (+56) | join-policy | Commit A (`y`) — eyeball |
| h5 | `get_final_report` (+35) | **visibility + turnaround** | **split** (C & E) |
| h6 | `commit_turn` (+20) | webhooks | Commit D (`y`) |
| h7 | `award_learning_bonus` | quiz | Commit B (`y`) |
| h8 | `award_learning_bonus` | quiz | Commit B (`y`) |
| h9 | `award_learning_bonus` | quiz | Commit B (`y`) |
| h10 | `get_peer_leaderboard` | analytics/visibility | Commit C (`y`) |
| h11 | `get_peer_leaderboard` | analytics/visibility | Commit C (`y`) |
| h12 | `get_peer_leaderboard` | analytics | Commit C (`y`) |

## `git add -p` key reference

Run `git add -p backend/router.py`. For each hunk:
- `y` stage it · `n` skip it (leave for a later commit) · `q` quit
- `s` split into smaller hunks (try before `e`)
- `e` edit the hunk by hand. In the editor:
  - to **NOT** stage an added line -> **delete** the `+` line
  - to **NOT** stage a removed line (keep it in the file) -> change its leading `-` to a space
  - leave context (space-prefixed) lines alone; save & close

After staging a feature's hunks, `git commit`, then repeat `git add -p` for the next.

---

## Recommended order

### Commit A — join-policy / consent
```
git add -p backend/router.py      # y on h0,h1,h2,h3,h4 ; n on the rest
git add backend/tests/test_medium_cohort_controls.py \
        backend/tests/test_advanced_cohort_controls.py
git commit -m "feat(cohort): MEDIUM-tier join policy, roster caps & consent"
```
Sanity: `python3 -m py_compile backend/router.py` and run the two tests.

### Commit B — quiz policy
```
git add -p backend/router.py      # y on h7,h8,h9 ; n on the rest
git commit -m "feat(quiz): per-cohort quiz attempts / pass threshold / grading"
```

### Commit C — result-visibility + peer analytics
```
git add -p backend/router.py      # y on h10,h11,h12 ; on h5 press 'e' (see below)
git add backend/tests/test_result_visibility_enforcement.py
git commit -m "feat(visibility): server-side report-access control + peer analytics"
```
**Editing h5** — keep the VISIBILITY lines, delete the TURNAROUND ones.

DELETE these `+` lines (they belong to Commit E):
```
    # P2: attach the score-based Turnaround offer (module flag + completion +
    # M_R threshold). Per-facilitator authorisation is applied by the admin
    # eligibility endpoint, not here (this endpoint has no role context).
    from admin_shared import _god_mode_settings as _gms
    from engine import turnaround_offer_for
    _turnaround_offer = turnaround_offer_for(gs, _gms.get("turnaround_module_enabled", False))
        "turnaround_offer": _turnaround_offer,
```
KEEP everything else in h5 — the `_report_access` block, the `facilitator_only`
locked return, `_withhold_narrative`, and the `report_access` /
`final_report_canonical` / `turnaround_amended_report` return fields. (The
`turnaround_amended_report` line is just `gs.get(...)` withholding — no turnaround
code needed, so it stays with visibility.)

### Commit D — webhooks (needs the untracked helper)
```
git add -p backend/router.py      # y on h6 only
git add backend/webhook_util.py
git commit -m "feat(cohort): LOW-tier round/game-over webhooks"
```

### Commit E — turnaround final-report wiring (the remainder of h5)
```
git add -p backend/router.py      # only the leftover h5 turnaround lines remain -> y
git commit -m "feat(turnaround): attach turnaround offer to the final report"
```
The turnaround engine itself is already committed (`e606eb4`); this just wires the
offer into `get_final_report`.

---

## After you're done
```
git diff HEAD -- backend/router.py     # should be empty (all hunks committed)
python3 -m py_compile backend/router.py
```
If an `e` edit goes wrong, `git checkout -p backend/router.py` safely discards
staged edits without losing the worktree file; re-run `git add -p` from scratch.

> Reminder: your index still holds the god-file **decomposition** for
> `admin_router.py` etc. (HEAD - 545 lines staged). The commits above use explicit
> pathspecs where they add companion files; a bare `git commit` (no pathspec) would
> also sweep that decomposition in, so either keep the pathspecs or unstage the
> decomposition first (`git restore --staged backend/admin_router.py ...`).
