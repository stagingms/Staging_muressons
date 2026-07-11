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
