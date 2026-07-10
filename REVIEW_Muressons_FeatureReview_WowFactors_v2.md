# Muressons — Feature Review v2 & Next-Generation Wow Factors

*Expert simulation-design review of the CURRENT tree (including your recent
uncommitted work), followed by wow-factor proposals that raise realism and
visual impact without touching round flow, scoring, or state sync. Review and
plan only.*

---

## 1. What you've added recently (reviewed)

Filtering EOL churn out of the diff, your real new work is a coherent
**industry-realism layer**:

- **Per-industry double-materiality libraries** — nine vertical configs
  (`backend/db/industry_configs/materiality_{agriculture, banking, oil_gas,
  retail_fmcg, technology, …}.json`) plus an Excel master
  (`industry_master_materiality.xlsx`) and an upload template — i.e., a
  data-driven pipeline where materiality content is authored in Excel, not
  code. This is the right architecture: content velocity without engine risk.
- **Richer DoubleMaterialityMatrix** (+300 lines) and a visually rebuilt
  **SimulationSwitchboard** (+240 + a new 460-line CSS module).
- **audit_api.py** expansion (+347) and vertical CSRD issue banks (+270).

**Verdict:** this closes what was previously the sim's weakest realism claim —
that every industry felt like re-skinned Muressons. With vertical-specific
materiality issues feeding the R2 CFO gate and the matrix exercise, an oil-&-gas
cohort now argues about stranded assets while a bank argues about financed
emissions. Two follow-through gaps to note: (a) **players never *see* the
industry library as a thing** — it powers one exercise and vanishes; W3 below
fixes that; (b) the upload pipeline needs the R3-style setup-integrity
treatment eventually (a bad Excel upload should fail loudly, per item).

## 2. Feature inventory — where the experience is dense vs thin

| Arc stage | What exists today | Density |
|---|---|---|
| **Onboarding** | Username → briefing → tour; R1 orientation gates (stakeholder map, board profiles); BU-specific podcast briefings | Strong |
| **Core loop** | Decision Canvas (Phase D), consequence previews + one-liners, prediction gate + confidence calibration, shared-dice determinism chip, What-If sandbox, IFRS balance sheet, engines tab, board-persona mailbox, crisis interstitials, round recaps, case cards | Very strong |
| **Mid-game theatre** | R5 Shadow Board, R6 revelation, R7 budget, R8 tribunal, side tracks ×6, black swans, Shockwave, TCFD/biodiversity | Strong at fixed beats; **thin between them** |
| **Endgame** | Terminal valuation + archetypes, Rewind Ribbon, Regret Meter, Archetype Card, Year-5 Front Page, CEO voice interview, Boardroom Showdown, Trading-Floor finale (bell/confetti/IPO deltas) | Exceptional |
| **Facilitation theatre** | Teleprompter (+podium mode), pulse heatmap, DNA comparison, teachable moments, consoles w/ per-facilitator gates | Strong |

**The three honest gaps** (these drive every proposal below):

- **G1 — The most-visible pixels are fake.** `MarketTicker` renders
  `Math.random()`-jittered static symbols (`BASE_ITEMS`) on every player
  screen, all session long — while the engine computes real WACC, internal
  carbon fee, inflation, green-fund balance, and a real share price
  (`stockValuationEngine`). The one element that *looks* most like a market
  is the only one that isn't.
- **G2 — The rival is a number, not a character.** `competitor_ebitda` and
  `relative_advantage` exist every round, but the competitor has no name, no
  face, no press releases — "vs Competitor 1.0×" is the entire antagonist.
- **G3 — Wow is endgame-loaded.** Rounds 2–4 and 6–9 have decisions and
  crises but no *artifact moments* — nothing a team screenshots mid-game.

---

## 3. Proposed wow factors (all flow-safe by construction)

Doctrine unchanged from v1: wow lives in the **ambient layer** (always on,
never blocking), the **artifact layer** (appears in results/debrief, never
gates), or the **facilitator-theatre layer** (projector, toggleable). Nothing
below adds a step to the commit path, alters timing, or writes game state.

### W1 — Kill the fake ticker: live market data 🔴 keystone · effort S-M
Replace `BASE_ITEMS` with symbols derived from state already on the client:
**MURS** (real share price from `stockValuationEngine`), **ESG Index** (cohort
reputation/SLO composite), **Carbon** (the internal carbon fee $/t actually
charged by the engine), **WACC** print, **CPI** (engine inflation index),
**Green Fund** balance. Deltas = real round-over-round moves. One file,
display-only, zero new fetches (dashboard data already in props).
*Why it matters:* every glance at the bottom of the screen becomes reinforcing
truth instead of decoration — and post-commit, the ticker visibly *reacts* to
what the team just did.

### W2 — Give the rival a face: "Nordhaven Group" · effort M
Pure presentation of existing engine outputs: (a) ghost line for competitor
EBITDA on the stock/EBITDA trend charts; (b) client-derived **rival press
releases** in the mailbox tab when `relative_advantage` crosses thresholds
("Nordhaven announces record margins as Muressons stumbles" — board-persona
styling, clearly marked as market news, computed from data already in
`globalState`, no state written); (c) a greyed rival row on the Trading-Floor
board. *Why:* antagonists create urgency; this one is free because the engine
already simulates it.

### W3 — Year-end Annual Report artifact · effort M-L ★ showcases YOUR new work
At each year boundary (post-R2/4/6/8 results), the results step offers
"📄 Year N Integrated Report ready" — a one-page, print-styled annual report
rendered in-app (Front-Page/Archetype-Card rendering pattern, PNG export):
financial highlights, emissions trajectory, covenant status, and — the new
part — **the team's top material issues from your per-industry materiality
library**, scored by how their decisions addressed them. *Why:* creates the
missing mid-game screenshot moments, teaches integrated reporting by making
one, and finally puts your industry-config investment on the player's screen.
Client-rendered from existing history data; appears only in the results step.

### W4 — Situation-Room bulletin (voice) · effort M
A 15-second, data-grounded market-news bulletin the facilitator can fire from
the Teleprompter between rounds — text assembled from the round's actual
events (crises fired, biggest mover, rival move), spoken via the ElevenLabs
plumbing the CEO interview already owns, over a chyron card on the projector.
Toggle in the Registry alongside Shockwave/Trading-Floor (the capability
pattern is now established). *Why:* professional-broadcast framing between
rounds is the cheapest large jump in perceived production value.

### W5 — Atmosphere engine + commit ceremony · effort S-M
Extend the existing health-based theme shift: climate tipping and crisis
states drive a subtle animated backdrop tier (CSS-only grain/ember drift,
`prefers-reduced-motion` safe, capped opacity); the commit button becomes a
**hold-to-commit turn-key** (600ms hold, mechanical click via CockpitSounds,
"BOARD RESOLUTION PASSED" stamp animation on the results card). *Why:* the
single most-repeated action in the game currently feels like a form submit;
ceremony at the moment of commitment is high perceived value per line of code.

### W6 — ESG rating-agency letters · effort M
Every even round, a **rating letter** (AAA→CCC, MSCI-style) appears as a
letterhead-styled card in the mailbox tab, derived client-side from existing
metrics (reputation, SLO, CI trajectory, governance risk) with an explicit
rationale line and an upgrade/downgrade arrow. *Why:* realism (this is how the
real world scores ESG), a recurring narrative thread, and a teachable artifact
— without touching the engine (pure derivation; same inputs ⇒ same letter,
so determinism holds).

### W7 — Region war-map (projector) · effort L
Your `region_id` / multi-region BU work has no map anywhere. A facilitator
projector view (`/admin/war-map`, same console pattern) with an SVG world map:
BU nodes by region, pulsing on crises, cyclone path animation in R5, black-swan
flashes. Data = existing leaderboard + events feed. *Why:* geography is the
one realism dimension currently invisible; projector maps photograph well.

**Rejected en route:** per-round social-share cards (dilutes the Archetype
Card's endgame punch); AI-generated imagery in reports (breaks determinism
story and adds latency); making W4 player-facing audio (uncontrollable
classroom soundscape — facilitator-triggered only).

---

## 4. Proposed plan

Same discipline as every phase so far: one commit per phase, endpoint-contract
diff, esbuild/ESLint/production build in-sandbox, unmodified player smoke,
pytest tripwire, revert = rollback. New surfaces default OFF or
facilitator-gated where noted.

| Phase | Contents | Risk | Key flow-safety test |
|---|---|---|---|
| **W-A** | W1 live ticker + W5 atmosphere/commit ceremony | Low (display-only, existing props) | Commit payload byte-identical; ticker shows real values matching dashboard; reduced-motion kills all of it |
| **W-B** | W2 rival presence + W6 rating letters | Low-Med (client derivations) | Same inputs ⇒ same outputs (determinism spot-check on a fixed session); mailbox tab renders derived cards without touching unread counts of real messages |
| **W-C** | W3 Annual Report artifact | Med (new render surface in results step) | Results step advance timing unchanged; report renders from history snapshot only; PNG export offline-safe; materiality section reads your industry configs read-only |
| **W-D** | W4 voice bulletin | Med (TTS reuse + Registry capability flag) | Follows the Shockwave capability pattern (server-gated 403); no player-side audio; teleprompter fetch contract additive-only |
| **W-E** | W7 war map | Med-High (new projector route) | Console pattern (own route, read-only feeds); zero player-surface change |

Sequencing rationale: W-A repays instantly and de-risks the ambient layer;
W-B/W-C build the narrative spine; W-D/W-E are theatre that can ship any time.
W-C is the one I'd prioritize pedagogically — it is also the phase that makes
your new industry-materiality investment visible to every player.

*Also recommended before any of this: commit your uncommitted work —
especially `admin/trading-floor/`, `admin/shockwave/`, and the industry-config
data files, which as untracked files have no git safety net (one was already
rescued from a corrupted read this week).*
