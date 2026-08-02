# Muressons — repo conventions

## Player-UI slotting rule (V-D, from REVIEW_Muressons_PlayerDashboard_v2_Simplification.md §3)

Every player-facing surface — existing or new — occupies **exactly one** slot.
A feature that ships as a new always-visible panel is a review defect, not a
style choice. The six feature waves that landed between the v1 redesign and
the v2 review each bought permanent screen space; this rule is what prevents
a v3.

| Slot | Rule |
|---|---|
| Canvas stage | Needed to complete the CURRENT stage of the round flow |
| KPI belt | Always-glanceable state (numbers + deltas only) |
| Expand drawer | Deep-dive detail, summoned not ambient |
| Rail tab (one open at a time) | Asynchronous context (mail, feed, intel) |
| ⋯ More menu | Occasional utilities |
| Projector/atmosphere layer | Facilitator theatre; dims under `data-allocation-open`; off <1280px |
| OverlayHost | Interrupts (crisis, shockwave, broadcast, tour) |

**In the same commit as any new player-facing UI:**
1. Name its slot (in the component header comment).
2. Use `app/styles/tokens.css` tokens — no raw hex for semantic colors
   (danger/success/caution), no new accent hues. Hue decisions happen on a
   real screen, never in a blind regex (see tokens.css Phase-B note).
3. Retrospective content (recaps, counterfactuals) renders in the results
   stage, not mid-decision (V-A precedent).
4. Locked/gated content renders as a locked summary naming its unlock —
   never full prose behind a click-intercept (V-B/V-C precedent).

## Sidebar tooltips (admin)
A tooltip must describe what the tab RENDERS today (three audits — G7,
Phase 6, V2-1 — each found aspirational tooltips). Change the tab, change the
tooltip, same commit. See `config/sidebarConfig.js` header.

## Shockwave catalog
`components/shockwaveCatalog.js` must mirror `backend/admin_router.py::_SHOCKWAVE_EVENTS`
— the jest tripwire (`__tests__/shockwave-catalog.test.js`) parses the backend
source and fails on drift. Update both in the same commit.

## Role model & RBAC

There is **one** authoritative role ladder, `ROLE_HIERARCHY` in
`backend/admin_shared.py`. It is mirrored in `frontend/app/config/sidebarConfig.js`
and the two are pinned equal by the drift tripwire
`backend/tests/test_role_hierarchy_sync.py` — change one, change the other, same
commit.

| Role | Level | What it is |
|---|---|---|
| `god_mode` | 4 | Virtual break-glass identity (master password). A **distinct top tier**, not an alias of super_admin. Not stored in the registry; granted only from the signed token. **Never assignable** to a registry facilitator. |
| `super_admin` | 3 | Full platform admin. |
| `admin` | 3 | Alias of `super_admin` (kept so the level is never undefined). |
| `lead_facilitator` | 2 | Facilitator plus overrides / undo / auto-pause. (NOT materiality — the Materiality Matrix editor is super-admin only.) |
| `facilitator` | 1 | Base simulation operator (own sessions). |
| `project_admin` | 0 | **Provisioning-only** role — creates facilitators + cohorts, NEVER manages runs. A **distinct role, OFF the run ladder** (level 0, below facilitator). Exists in **two forms** (RBAC-F5b): a *virtual* break-glass identity via `PROJECT_ADMIN_PASSWORD` (one shared secret, no individual accountability — disabled when the env var is unset), and a *registry* account (`FAC-NNN` with `role: project_admin`, assignable by a super_admin) which is the preferred form for a named programme administrator because it is per-person, auditable and revocable. Both behave identically at every guard. |
| *Player* | — | **Separate authz realm** — not in `ROLE_HIERARCHY`. Authenticated via `X-Player-Id` + session-ownership (SEC-3), never a facilitator role. |

Conventions when touching auth:

1. **god_mode ≥ super_admin by level, so use the level, not the string.** For any
   "is this an admin?" decision use `is_admin_role(role)` (level ≥ super_admin),
   never `role == "super_admin"` — the latter silently drops god_mode. Level-gated
   guards (`require_super_admin`, `require_lead_facilitator`) already pass god_mode
   automatically because 4 > 3 > 2.
2. **Run management gates on `require_sim_manager`, not `require_facilitator`.**
   `require_facilitator` admits project_admin; `require_sim_manager` excludes it.
   Every endpoint that operates a *live run* (pacing, unlock, player mgmt, live
   interventions, grading, notes) must use `require_sim_manager`. Cohort
   *provisioning/config* endpoints (bu-composition, side-tracks, cohort pacing
   defaults, pedagogical settings, ending-pathway, CEO-interview) stay on
   `require_facilitator` because project_admin performs them while provisioning.
3. **Role assignment is caller-scoped.** `create_facilitator`,
   `bulk_create_facilitators`, `update_facilitator` and `update_facilitator_role`
   must validate the requested role against `assignable_roles_for(caller_role)`:
   a caller may never grant a role above its own tier, `project_admin` may grant
   only `lead_facilitator`/`facilitator`, and `god_mode` is never grantable by
   anyone.
4. **Provisioning implies impersonation — that is the trust model, not a bug**
   (RBAC-F5b). Whoever creates an account learns its initial credential (it is
   returned once, and defaults are the deterministic `FAC-NNN@321`). A
   `project_admin` can therefore mint a `lead_facilitator` and sign in as it
   before the real person does, gaining run rights its own role forbids.
   `must_change_password` makes the takeover visible (the rightful owner finds
   their default rejected), and project_admin cannot mint admin tiers or another
   project_admin, so it cannot spread. Give project_admin only to someone you
   would be willing to make a lead facilitator. To make it strictly weaker,
   narrow its grants to `facilitator` in `assignable_roles_for` — one line.
5. **Cohort SHELL vs cohort ROSTER is a deliberate seam** (RBAC-F6).
   `project_admin` may create a cohort (`/simulations/start`) but every
   player-id mint is `require_sim_manager`, which excludes it — player ids are
   live-run credentials, so issuing them is run management. A cohort handed over
   with an empty roster is a COMPLETE provisioning deliverable; the facilitator
   who runs it generates and distributes the roster. If this ever needs to
   change, widen `generate-player` only for a not-yet-started cohort (round 1,
   no players joined) — the same pre-start window `patch_session_metadata`
   already uses — never for a live run.
