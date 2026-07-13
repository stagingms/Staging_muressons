# Role-Aware Login — Plan & Implementation Approach

*Grounded in the current tree (branch `ux/v3-phases`). Goal: nobody sees a
portal that isn't theirs — god_mode and project_admin must be invisible to
facilitators. Hard constraint: **simulation logic, participant/player realm,
and the server-side RBAC (ROLE_HIERARCHY + `require_*` guards) stay byte-for-byte
unchanged.** This is a login-UX + client-routing change only; the server
remains the authoritative gate (defense in depth).*

---

## 1. The actual problem (verified in code)

`frontend/app/admin/page.js` is the "System Access Portal" in your screenshot.
It is a **static, unauthenticated Next server component** that renders two
`<Link>` cards — "👑 God Mode — Super Admin" → `/admin/god-mode` and
"🎓 Workshop Facilitator" → `/admin/facilitator`. It advertises the privileged
portal to *everyone who loads the page* and asks the user to **self-select a
portal before authenticating.**

That self-selection is the whole bug. You cannot hide a role from a facilitator
on a page that, by design, shows every role's door before anyone has logged in.
Two consequences:

- **Visibility:** a facilitator (or any visitor) sees "God Mode — Super Admin."
- **Minor info-disclosure:** an unauthenticated page enumerates a privileged
  entry point (matches the kind of thing the comprehensive review flags).

What is *already* correct and must be preserved:

- The login endpoint `/api/admin/facilitators/login` returns an authoritative
  `role` for **every** identity — `god_mode` (1815), `super_admin`,
  `lead_facilitator` (1823), `facilitator`, `project_admin` (1831), plus the
  final response `role` (1880). The client never decides the role; the server
  does, and the JWT cookie + `require_*` guards enforce it.
- The god-mode page's login gate already **rejects** non-admins after login
  (`data.role !== 'super_admin' && !data.is_admin`, god-mode/page.js:88). So a
  facilitator physically cannot get *into* god mode even today — the defect is
  purely that the gateway *shows* them the door.
- The facilitator page already renders the **project_admin** provisioning view
  inline from `allowed_tabs` (registry + cohort provisioning only) — role-
  adaptive, no separate portal needed.

---

## 2. The redesign — identity-first, role-derived

**Invert the flow.** Replace "pick a portal, then log in" with "log in, then be
routed." One login form (the same ID + password both gates already use, the
same endpoint, the same `credentials:'include'`). On success, read the
server-returned `role` and send the user to the single dashboard that role owns.

```
            ┌─────────────────────────────┐
            │   /admin  —  Sign in         │   one form, no portal cards
            │   Facilitator ID + Password  │   (god_mode/project_admin
            └───────────────┬─────────────┘    NEVER named pre-auth)
                            │ POST /facilitators/login  (unchanged)
                            ▼
                 server returns { role, … }   ← authoritative
                            │
        ┌───────────────────┼───────────────────────┐
        ▼                   ▼                        ▼
  super_admin/god_mode   project_admin        facilitator / lead_facilitator
        │                   │                        │
        ▼                   ▼                        ▼
   /admin/god-mode    /admin/facilitator        /admin/facilitator
                      (provisioning view,      (role-filtered sidebar,
                       via allowed_tabs)        exactly as today)
```

A facilitator never sees "God Mode" because **there is no card to see** — just a
login form. A super_admin reaches god mode by logging in with the same form and
being routed there automatically. project_admin lands on the provisioning view
it already has. No pre-auth surface ever names god_mode or project_admin.

**Why this is safe:** the routing is a client convenience for a *good*
experience; it is **not** the security boundary. The security boundary is
unchanged — the JWT cookie, `is_admin_role()`, `require_super_admin` /
`require_sim_manager` / `require_facilitator`, and the player realm (SEC-3) all
stay exactly as they are. If someone deep-links or forges client state, the
server still rejects them. This plan only removes the *advertising* and adds
*convenience routing*.

---

## 3. Implementation approach (phased, low-risk)

Same protocol as the S/V phases: one commit per phase, jest + `next build` +
player smoke, endpoint-contract unchanged (the login request/response is
untouched), `git revert` rollback.

### Phase L1 — Unified login component (no behaviour removed yet)
Extract the identical login form already living in *both* gates
(`GodModeLoginGate`, the facilitator `FacilitatorLoginGate`) into one
`components/AdminLogin.js`: ID + password, `POST /facilitators/login`,
`credentials:'include'`, error handling, the existing `PasswordInput` +
caps-lock affordances. Add a tiny `roleHome(role, is_admin)` helper (the single
source of truth for "where does this role live"), mirroring the
sidebar/guard model:
- `super_admin | admin | god_mode` (or `is_admin`) → `/admin/god-mode`
- everything else (`facilitator | lead_facilitator | project_admin`) →
  `/admin/facilitator`
**Test:** component renders; login still succeeds; no routing wired yet.

### Phase L2 — Turn `/admin` into the single sign-in
Replace the two-card gateway with `<AdminLogin>`. On success, `router.push(roleHome(...))`.
Delete the "God Mode — Super Admin" and "Workshop Facilitator" cards and the
`gateway.module.css` role-advertising styles. `/admin` is now a login, not a
directory.
**Test:** unauthenticated visitor to `/admin` sees only a sign-in form — no
role names, no god_mode/project_admin anywhere in the DOM; each identity logs
in and lands on the right dashboard (role matrix below).

### Phase L3 — Deep-link hygiene on the destination pages
The two dashboards keep their own login gates (for refresh / direct nav), but:
- `/admin/god-mode`: if a **logged-in non-admin** lands here (old bookmark),
  redirect to `/admin/facilitator` instead of showing the current error text —
  a facilitator should never be *stranded* on a god-mode error screen. (The
  server already 403s their god-mode API calls; this is just UX.)
- both pages: when **unauthenticated**, render `<AdminLogin>` (or redirect to
  `/admin`) so there is exactly one login surface and it never names a role.
**Test:** logged-in facilitator navigating to `/admin/god-mode` is bounced to
their dashboard; unauthenticated visits to either page show the neutral login.

### Phase L4 — (optional) Copy + polish
Neutral sign-in copy ("Sign in to the Muressons facilitator console"), no
mention of tiers. Keep the master-password break-glass path working (god_mode
via master password on the same form routes to god-mode — unchanged, intended).

---

## 4. Constraint checklist — what must NOT change

- **Server RBAC:** `ROLE_HIERARCHY`, `is_admin_role`, every `require_*` guard,
  `assignable_roles_for`, the player realm — untouched. (CLAUDE.md §"Role model
  & RBAC" stays the authority; this plan doesn't touch it.)
- **Login endpoint contract:** same request, same response — no backend edit.
- **Participant/player flow:** separate realm, separate routes — untouched.
- **project_admin capabilities:** unchanged; it still lands on the provisioning
  view it already renders from `allowed_tabs`.
- **Break-glass:** master-password → god_mode still works and routes correctly.

## 5. Test matrix (run at L2/L3)
- Log in as each of: base facilitator · lead_facilitator · super_admin ·
  project_admin · god_mode (master pw) → each lands on the correct dashboard;
  none can see another's portal name anywhere pre- or post-auth.
- Unauthenticated: `/admin`, `/admin/god-mode`, `/admin/facilitator` all show
  the neutral sign-in; "god mode" / "project admin" absent from page source.
- Deep-link: logged-in facilitator → `/admin/god-mode` → redirected out; a
  crafted god-mode API call still returns 403 (server, already true — verify).
- Regression: jest, `next build`, player smoke unchanged.

## 6. Why not the alternative ("just hide the God Mode card for facilitators")
You can't — the card renders before login, when the visitor's role is unknown.
Any client-side "hide for facilitators" would still ship the card in the page
and could be revealed by disabling JS. The only correct answer is to not
advertise portals pre-auth at all and route by the server-verified role. This
is also less code (one login, not two gates + a directory) and closes the
info-disclosure surface for free.

---

*Recommendation: implement L1–L3 as one short phase (call it **L**), L4 as
polish. It's ~2 files of new/changed frontend, zero backend, and revert-clean.
Ready to build it on your go.*
