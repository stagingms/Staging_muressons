# UX v3 — Phase S0 Baseline (evidence record)

Branch: `ux/v3-phases` (from `main` @ `141a331`). Baseline commit: `ec908f9`
(review doc only — **zero code changes in S0**). Run in-sandbox 2026-07-11,
memory-DB mode (`USE_MEMORY_DB=true`), server killed after each capture —
no residue in any persistent store.

This file is the regression oracle for Phases S1–S5 of
`REVIEW_Muressons_UIUX_v3_NewSurfaces.md`.

---

## 1. Backend test suite — green count

`python3 -m pytest tests/ -q` → **976 passed, 0 failed** (1 warning).
The v1/v2-era count was 961; the +15 arrived with the WOW / project_admin /
security commits, all pre-dating this UX work. **Every phase must end at 976.**

## 2. Player E2E smoke — `archive/root/test_api_flow.py`, unmodified

Against a live in-sandbox backend: solo-start → dashboard (4 BUs, $50M treasury,
`multi_toggles`) → TCFD scenarios → pillar config → R1 crisis + 5 pillar
decisions → ConsequencePreview (6 impact bars, PASS) → commit → treasury/carbon
KPIs update → TCFD post-commit + Biodiversity / Balance-Sheet / Board-Governance /
Supply-Chain engines all OK → **R2 commit: HTTP 429**.

⚠️ Baseline fact: the R2 commit's 429 is the commit rate-limiter (security
patches) reacting to the script's immediate-fire timing — it is **expected** and
must still be 429 after every phase. A change to 201 or 4xx-other is a regression
either way.

## 3. Endpoint-contract snapshot

`UX_V3_S0_endpoint_contract.txt` — static extraction of all **303** `fetch(` /
`new WebSocket(` call sites across `frontend/app` (213 in the two admin pages;
player files included deliberately so the oracle also catches accidental
player-side edits). Rule: after each phase, regenerate with the same command
(header of the file) and diff; every delta must be listed in the phase notes.
Only S4 (rehearsal flag) and S5 (sign-off-gated backend items) may add anything.

## 4. Console payload capture — throwaway cohort, real detonation

Facilitator: seeded `FAC-001` (lead_facilitator). Cohort: "Bulletin Test's Alpha
Cohort (FAC-001)". Player inducted via `POST /api/admin/players/induct`
(`MUR-001`) and joined via `POST /api/simulations/public/sessions/{id}/join`.

### 4a. Shockwave (S3's confirm must gate an identical request)
- Request: `POST /api/admin/{cohort_id}/shockwave` · body `{"event_id":"pandemic","countdown":60}`
- Response: `{"status":"detonated","event_id":"pandemic","teams_hit":1,"event":{"title":"Global Pandemic Shockwave","financial_impact":-6000000,"reputation_impact":-6,...}}`
- KPI evidence (the throwaway team): treasury **12,500,000 → 6,500,000**
  (Δ −6,000,000 exactly), reputation **50.0 → 44.0** (Δ −6 exactly).
- Drift-tripwire baseline (G-3): the console's hardcoded card strings
  ("−$6.0M · −6 rep" etc.) match `_SHOCKWAVE_EVENTS` today. Values recorded for
  the four events: pandemic −6.0M/−6 · carbon_tax −5.0M/−3 ·
  supply_collapse −4.5M/−4 · cyber_attack −4.0M/−7.

### 4b. Ring the Bell (S3's confirm must gate an identical request)
- Request: `POST /api/admin/{cohort_id}/finale/ring-bell` · no body
- Response: `{"status":"bell_rung","cohort_id":"<cohort>"}`
- Reminder of verified scope (review F-3): the server broadcasts `market_close`
  to **all** students and the player client does not filter by cohort_id —
  the S3 confirm copy must state this; the data flow itself is unchanged.

### 4c. Rehearsal probe (S4's no-op claim, proven at baseline)
- Request: `POST /api/admin/{cohort_id}/shockwave` · body `{"event_id":"cyber_attack","countdown":30,"rehearsal":true}`
- Response: `{"status":"rehearsal", "message":"Rehearsal only — students NOT affected", ...}` (HTTP 200)
- Player KPIs before/after: **byte-identical** (treasury and reputation
  unchanged). This is the S4 acceptance reference.

Full raw capture (login/induct/join/shockwave/bell/rehearsal, statuses and
bodies): see §7 appendix.

## 5. Items that can only run on your machine (do before merging S1)

The sandbox has no browser, so two S0 artifacts are yours:

1. **Screenshot set** — both dashboards (every tab you use live) plus the three
   consoles in each state: OFF / error (backend stopped) / live / (trading floor
   only) closed-after-bell. Suggested: one folder `docs/screenshots/ux-v3-s0/`.
2. **HAR captures** — dev-tools network export while walking: facilitator
   dashboard (login → select cohort → teleprompter → leaderboard → one
   broadcast), god mode (overview → a settings toggle → danger zone view), and
   each console (load → enable → one poll cycle; for trading floor also one
   bell ring on a throwaway cohort). These complement the static extraction
   with real payloads/cadences.
3. **Two-browser reference video/notes** (optional but recommended): facilitator
   + player side by side; one shockwave and one bell on a throwaway cohort —
   the player-side visuals are the reference S3's "identical behavior" check
   compares against.

## 6. Rollback

S0 changes nothing: rollback = `git checkout main`. The branch carries only
documentation (`REVIEW_…v3…md`, this file, the contract snapshot).

## 7. Appendix — raw capture (trimmed)

```json
{
  "auth": {
    "status": 200,
    "role": "lead_facilitator",
    "must_change_password": false
  },
  "throwaway_cohort": {
    "session_id": "d5469db7-6f03-422e-8c9c-72c0755cc197",
    "name": "Bulletin Test's Alpha Cohort (FAC-001)"
  },
  "induct_join": {
    "induct": {
      "status": 200,
      "player_id": "MUR-001"
    },
    "join_status": 200
  },
  "shockwave": {
    "request": {
      "method": "POST",
      "url": "/api/admin/{cohort_id}/shockwave",
      "body": {
        "event_id": "pandemic",
        "countdown": 60
      }
    },
    "status": 200,
    "response": {
      "status": "detonated",
      "event_id": "pandemic",
      "teams_hit": 1,
      "event": {
        "title": "Global Pandemic Shockwave",
        "narrative": "A novel pathogen halts supply chains overnight. Every division must respond \u2014 now.",
        "financial_impact": -6000000,
        "reputation_impact": -6
      }
    }
  },
  "kpi_evidence": {
    "before": {
      "treasury": 12500000.0,
      "reputation": 50.0
    },
    "after": {
      "treasury": 6500000.0,
      "reputation": 44.0
    },
    "delta": {
      "treasury": -6000000.0,
      "reputation": -6.0
    }
  },
  "ring_bell": {
    "request": {
      "method": "POST",
      "url": "/api/admin/{cohort_id}/finale/ring-bell",
      "body": null
    },
    "status": 200,
    "response": {
      "status": "bell_rung",
      "cohort_id": "d5469db7-6f03-422e-8c9c-72c0755cc197"
    }
  },
  "rehearsal_probe": {
    "status": 200,
    "response": {
      "status": "rehearsal",
      "event_id": "cyber_attack",
      "event": {
        "title": "Coordinated Cyber Attack",
        "narrative": "A ransomware wave locks systems sector-wide. Operations stall and trust is shaken.",
        "financial_impact": -4000000,
        "reputation_impact": -7
      },
      "message": "Rehearsal only \u2014 students NOT affected"
    },
    "kpis_unchanged": true
  }
}
```
