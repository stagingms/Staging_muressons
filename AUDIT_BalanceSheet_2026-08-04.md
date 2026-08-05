# Muressons — Balance Sheet & Financial Statement Audit
**Date:** 2026-08-04 · **Auditor roles:** accounting professor / practising auditor / three-statement modeller
**Scope:** `backend/balance_sheet.py`, `backend/engine.py`, `backend/round_logic.py`, `backend/router.py` (commit path), `backend/config.py`, `backend/terminal_valuation.py`, executed over full 10- and 20-round simulated runs.

---

## 0. The "fill-in" answers, established from the artefact itself

The request template's required fields were not supplied, so I established them from the repo and state them here rather than assuming silently:

* **Declared framework: IFRS — confirmed by the owner during this audit.** The code already claims it: `balance_sheet.py:6-16` cites IAS 1 / IAS 16 / IAS 36 / IAS 37 / IAS 38 / IFRS 16; `SIMULATION_CONTEXT.md` §12 lists "Balance Sheet Engine — IAS 1 format". The audit therefore holds the model to IFRS as the binding standard (not merely internal consistency), and departures from IAS 36/38/IFRS 16/IAS 12 are classified as ERRORS unless they qualify as declared, safe simplifications. Where a verdict would soften under "generic teaching conventions" I still note it, for context only.
* **Statements produced:** a Statement of Financial Position (full line items, per round, with history snapshots); an income statement that exists only inside `diagnostics["income_statement"]` (`balance_sheet.py:792-807`) and the per-round history rows; and a **treasury "consequence waterfall"** (`engine.py:3755-3760`) which is the de-facto cash flow statement. **NOT FOUND: a classified cash flow statement (operating / investing / financing).** I searched `engine.py`, `round_logic.py`, `router.py`, `balance_sheet.py` for `cash_flow` / `cashflow` / statement-of-cash-flows constructs; none exist.
* **Where the logic lives:** `balance_sheet.py` (statement build, 943 lines); `engine.py::process_tick` (treasury/cash, 4,249 lines); `round_logic.py::post_tick` and `::run_new_engines` (round impacts; BS engine invocation at 621-678); `router.py::commit_turn` (orchestration; BS inputs injected at 2543-2544); constants in `config.py:135-209, 561-565`.
* **Round cadence:** 10 rounds × 6 months = 5 years (`SIMULATION_CONTEXT.md` §1). Rates are mostly halved per round; the exceptions are themselves findings (E9, I1).
* **Student level:** executive / MBA (`SIMULATION_CONTEXT.md` §1).
* **Declared deliberate simplifications found in code comments:** ESG capitals off-BS with a scholarly on-BS toggle; negative-cash sweep to short-term debt; EBITDA floor at 0 in terminal valuation; dividend clamp to available cash; no deferred tax, no FX balance-sheet effects, no minority interest (absent rather than declared). These are assessed in §4, not condemned.

---

## 1. Overall verdict and confidence

**Verdict:** The balance sheet always balances, and that is precisely the problem: **retained earnings is an explicit plug** (`balance_sheet.py:823-841` — "treat retained earnings as the CLOSING / RESIDUAL equity figure"; assignment at line 840, re-derived again at 905 after the covenant surcharge). Every asset, liability and cash movement that has no double entry — and there are many — is silently absorbed into equity, and `diagnostics["balance_sheet_balanced"]` is hard-coded `True` (line 844). Measured over a production-faithful 10-round run, the gap between the retained-earnings movement and (net income − dividends) ranged from **−$12.0M to +$333.5M per round** (§3, Test 2). Underneath the plug sit real articulation errors: CAPEX creates PP&E without ever reducing cash or creating debt; dividends are recorded in equity at the *requested* amount while cash pays the *clamped* amount; goodwill impairment, brand revaluation and lease-liability amortisation all bypass the income statement; tax is expensed but never paid; and the de-facto cash flow statement leaves up to $55M per round of cash movement unexplained. The individual "FIX-1…13" repairs documented in the module header are mostly real and mostly good — but they were fitted around a hybrid cash/accrual architecture whose two halves (`engine.py` treasury vs `balance_sheet.py` statement) were never articulated, and the plug is what hides that.

**Overall confidence: High** for every engine-level finding (each is cited to file:line and reproduced by executed code below). **Medium** for exact production magnitudes: my harness replicates `router.commit_turn`'s pipeline (`process_tick → post_tick → events injection → run_new_engines → reporting resync`, mirroring `tests/test_financial_golden_trace.py` and `router.py:2402-2612`) but omits the router's pillar-aggregation deltas, so production residuals will differ in size, not in kind. The player-facing frontend was not audited (see §9).

---

## 2. Model Map (Phase 0)

### 2.1 Balance sheet line items — source, stock-vs-fresh, sign

All values are positive-signed within their section; assets positive, liabilities positive, equity positive (assets − liabilities = net_assets). One tick = `process_balance_sheet_tick` (`balance_sheet.py:512`), invoked from `run_new_engines` (`round_logic.py:655`) after `process_tick` and `post_tick`.

| Line | Source | Stock or fresh? | Evidence |
|---|---|---|---|
| PP&E | opening + 60% of round CAPEX − 5% of opening balance | **Stock (rolls)** | :575-592 |
| Inventory | `total_opex/365 × 60` | **Fresh each round** (formula) | :610-611 |
| Right-of-use assets | opening × 0.975 | Stock (decays) | :594-598 |
| Brand value | `base × (rep/50) × sqrt(SLO/50)`, floor $1M — revalued against a fixed base | **Fresh** (revaluation) | :270-303, 638-641 |
| Intellectual property | seed value, never touched again | Static | :137, 203 |
| Goodwill | opening − impairment every 2nd round (dual trigger, ≤30%) | Stock (decays) | :686-712 |
| Cash | `max(0, corporate_treasury)` after sweep | **Synced from engine** | :559, 480-509 |
| Trade receivables | `revenue × min(0.25, 0.12+0.001×gov_risk)` | **Fresh** | :613-615 |
| Prepayments | seed $250K/BU, never updated | Static | :147 (only write) |
| Revolving credit facility | seed $12.5M/BU, **never changes** | Static | :128, 216 (only writes) |
| Green bonds | += on issuance event | Stock (grows only; no redemption) | :737-740 |
| Environmental provisions | `NCD×$5K + events×$2M`, floor $1M — remeasured | Fresh (remeasurement) | :359-386, 730-734 |
| Decommissioning obligations | opening × (1 + 1.5%/round accretion) | Stock (grows) | :747-756 |
| Lease liabilities | opening × 0.975 | Stock (decays) | :742-745 |
| Trade payables | `opex × min(0.18, 0.10+0.0005×gov_risk)` | **Fresh** | :617-619 |
| Tax provisions | `max(0, gross_profit × 25% × 20%)` | **Fresh** — unrelated to the P&L tax charge | :621-624 |
| Accrued remediation | seeded 0, never written | Dead line | :225 (only write) |
| Short-term debt | **SET** (not +=) to the cash deficit each tick | Fresh (sweep) | :480-509 |
| Share capital | seed $7.5M/BU, static — no issuance mechanic exists | Static | :133, 230 |
| Other reserves | seed $1.25M/BU, static | Static | :134, 232 |
| **Retained earnings** | **`net_assets − share_capital − other_reserves` — a plug** | Derived residual | **:840, :905** |
| ESG capitals | SLO×$200K, rep×$300K — off-BS disclosure (on-BS only under scholarly toggle) | Fresh | :644-684 |

### 2.2 Round-resolution order (the money path)

Verified by reading `router.py:2402-2612` and `engine.py:2283-2293` (pipeline comment), and executed end-to-end:

1. `process_tick` — **stochastic layer**: black swans, cannibalisation, supply chain, macro rates, FX, **DSO deferral (permanently subtracts 2–12% of `revenue_base`; cash returns next round via a pending project — `engine.py:2473-2491`)**, **cash-conversion drag (permanently multiplies `revenue_base` by 0.88–1.0 — `engine.py:2496-2501`)**, inflation.
2. **Financial layer**: synergy OPEX; **dividends clamped to treasury** (`:2593-2594`); CSF = Σ(rev−opex) − dividends (`:396-402`); CAPEX cap/overrun; loan interest on CAPEX above 20% of treasury; **treasury = opening + CSF − interest** (`:2678`) — *CAPEX principal is never deducted*; pending-project completions; negative-treasury debt service and the **treasury floor** (−$500M + ESG relief, `:3005-3015`, config.py:170).
3. **Operational layer**: carbon fees, CBAM, offsets, levies — all charged to treasury, none to any P&L.
4. **Reporting layer**: greenwashing fines, distress/bailout (`:3628-3640`), final treasury floor re-clamp (`:3727-3730`), **waterfall finalised here** (`:3755-3760`) — everything after this point moves cash *outside* the waterfall.
5. `post_tick` — round-specific crisis impacts hit treasury directly (e.g. R1: −$8.0M measured, waterfall drift table §3 Test 3).
6. Router injects `events["decisions_raw"]` and `events["dividends_paid"] = body.dividends_paid` (**requested**, not clamped — `router.py:2543-2544`).
7. `run_new_engines` → `process_balance_sheet_tick`: cash sync → sweep (+interest) → CAPEX capitalisation (60%) → depreciation (5% of opening PP&E; ROU 2.5%) → working-capital re-derivation → brand/goodwill → provisions/leases/accretion → P&L (interest = debt × ESG-WACC/2 + accretion; tax = max(0, 25% × taxable)) → totals → **RE plug** → covenant check + surcharge → re-derive totals and **plug again**.
8. Router reporting-truth resync recomputes `historical_ebitda`, `tco2e` from the final BU table (`router.py:2583-2590`).

Order-of-operations findings: depreciation correctly uses opening PP&E before the round's CAPEX (FIX-5 works — verified, Test 4 residual $0.00 every round); interest in the BS P&L is charged on the *current mid-tick* debt (post-sweep short-term debt, closing-ish revolver), while the engine charges four *other* interest streams at other rates and conventions (I1).

### 2.3 Articulation graph — where it is severed

* Income statement → retained earnings: **severed by design.** NI is computed (`:788`), preserved in diagnostics, and explicitly *not* posted to RE (`:783-790`, `:823-841`).
* Cash flow → cash: cash *is* the treasury (synced), so the BS cash line is always right; but the *statement* of that flow (waterfall) closes mid-pipeline and misses post_tick and BS-engine charges — measured miss up to **$55.4M in one round**, $161M total over 10 rounds (Test 3).
* Decisions → line items: CAPEX → PP&E (60%) works; dividends → equity works in direction but at the wrong amount when clamped (E3); investment_ratio → OPEX via synergy works; green bond decision → liability works; **no decision anywhere maps to the revolver, share capital, or a debt repayment — no repayment mechanic exists in the codebase** (searched: `repay|principal_repaid|debt_repayment` — only a covenant message string matches).

### 2.4 The plug — headline answer

**A plug exists, and it is retained earnings.** `balance_sheet.py:840` (`bs["retained_earnings"] = round(bs["net_assets"] - fixed_equity, 2)`), repeated at `:905`; rationale comment at `:823-841`; `balance_sheet_balanced` hard-coded `True` at `:844` with `imbalance: 0.0` at `:845`. This is a documented, deliberate plug — which means A = L + E is *tautological* and every reconciliation failure in §3 is invisible on the face of the statements. Real errors (E2–E9) are being masked exactly as the plug-warning in the brief anticipated.

### 2.5 Round-1 opening position

`create_initial_balance_sheet` (`:108-263`): all lines set to grounded values, PP&E derived to close the equation (Option B), then RE derived — so opening RE is exactly $0 unless the PP&E floor (`max(0.30×revenue, derived)` at `:187`) binds, in which case the floor's excess lands in opening RE. **Executed check: opening A = 128,250,000.00, L = 93,250,000.00, E = 35,000,000.00, A−L−E = 0.00, RE = 0.00** (Test 10). The opening position balances. (Note the seed uses a revenue-proxy for trade payables while the tick uses an OPEX-based DPO — a small internal inconsistency between the opening and every later round, `:152-153` vs `:617-619`.)

---

## 3. Reconciliation test results (Phase 1) — executed, not reasoned

Harness: `audit/run_trace.py` — replicates the commit pipeline exactly as `tests/test_financial_golden_trace.py` does, **plus** the router's `events["decisions_raw"]/["dividends_paid"]` injection (router.py:2543-2544) which the golden trace itself omits (see §9). Seeded (20260802), 10 rounds, the golden-trace decision script, $500K dividends from R2. All figures below are from actual runs (`audit/recon.py`, `audit/re_bridge.py`, `audit/edges.py`).

### Test 1 — Fundamental identity A = L + E

Residual **0.00 in all 10 rounds** — *by construction* (RE plug). Recomputed totals from line items also matched stored totals to the cent in all rounds (no subtotal-range bugs). **Meaningless as evidence of correctness; reported for completeness.**

### Test 2 — Retained earnings roll-forward: RE_open + NI − dividends = RE_close

| Rnd | RE_open | NI | Div | RE_close | **Residual** |
|---|---|---|---|---|---|
| 2 | 68,403,961.94 | −12,001,015.80 | 500,000 | 70,237,391.83 | **+14,334,445.69** |
| 3 | 70,237,391.83 | −19,047,147.46 | 500,000 | 50,284,520.67 | **−405,723.70** |
| 4 | 50,284,520.67 | −31,589,379.33 | 500,000 | 27,669,535.78 | **+9,474,394.44** |
| 5 | 27,669,535.78 | −44,684,849.12 | 500,000 | −18,479,497.75 | **−964,184.41** |
| 6 | −18,479,497.75 | −69,428,602.24 | 500,000 | −96,647,338.88 | **−8,239,238.89** |
| 7 | −96,647,338.88 | −111,528,575.59 | 500,000 | −219,339,502.02 | **−10,663,587.55** |
| 8 | −219,339,502.02 | −206,838,195.33 | 500,000 | −424,133,818.32 | **+2,543,879.03** |
| 9 | −424,133,818.32 | −328,452,180.28 | 500,000 | −419,584,838.66 | **+333,501,159.94** |
| 10 | −419,584,838.66 | −58,567,106.33 | 500,000 | −426,543,097.17 | **+52,108,847.82** |

**FAILS every round.** The R9 residual of +$333.5M coincides with the engine's treasury floor re-clamping a ~−$750M implied position back to −$380M (floor = −$500M + 0.6×$200M ESG relief; `engine.py:3015, 3727-3730`, `config.py:170`) — a third of a billion dollars of equity appears from a clamp and the statements show nothing.

**Residual decomposition (executed, `audit/re_bridge.py`, e.g. Round 4, residual +9,474,394.44):** brand revaluation +10,194,741.96 (no P&L), goodwill impairment −2,701,476.62 (no P&L), lease liabilities −528,731.44 (liability decays with no P&L and no cash — pure equity gain), working-capital re-derivations ±, cash-vs-accrual gap. The itemised deltas sum exactly to ΔRE in every round tested (bridge closes to the cent), proving the residual is fully attributable to movements that bypass the income statement.

### Test 3 — Cash

* BS cash = `max(0, treasury_close)`: **holds every round** (sweep works as specified).
* Waterfall ("cash flow statement") final vs actual closing treasury — **unexplained drift**: R1 −8,000,000.00 (post_tick crisis); R4 −6,847,845.63; R7 −28,851,267.00; R8 −38,028,947.50; **R9 −55,351,996.52**; total |drift| over 10 rounds = **$161.3M**. Cause: waterfall is finalised at `engine.py:3755` but treasury keeps moving in `post_tick` (crisis impacts, `round_logic.py:262-273, 843-850`) and in the BS engine (sweep interest `balance_sheet.py:504-509`, covenant surcharge `:878-887`).

### Test 4 — PP&E roll-forward
`PPE_open + 0.60×capex − 0.05×PPE_open = PPE_close`: residual **0.00 all rounds**. Ties exactly. (No disposals mechanic; none claimed. No accumulated-depreciation account; the model presents net book value only and does not claim otherwise.)

### Test 5 — Debt
Revolver: **$50,000,000 in every round of every scenario — static**. Green bonds: 0 (no issuance event in this script; += verified by code read only). Short-term debt: equals the swept cash deficit to the cent every round (R5 24,401,892.23 … R9 435,351,996.52). **Meanwhile the engine's CAPEX "loan_principal" (engine.py:2661-2672) appears on no statement and is never repaid.**

### Test 6 — Inventory / receivables / payables
Recomputed from the closing BU table via the stated formulas: residual **0.00 all rounds**. These are *formula proxies, not roll-forwards* — there is no purchases/COGS articulation and none is claimed internally (but nothing tells the student, see P-findings).

### Test 7 — Income statement internal arithmetic
`taxable = gross − interest − dep − capex_expensed`, `tax = max(0, 25%×taxable)`, `NI = taxable − tax`: residuals **0.0 all rounds** — internally consistent. Interest recompute matched to the cent in R1–R4; from R5 a residual (−306K…−3.5M) appears because interest is computed on the *mid-tick* short-term-debt balance while the covenant-surcharge re-sweep changes the closing balance afterwards (`:770-778` vs `:887`). BS `tax_provisions` (e.g. R1 726,533.51) ≠ P&L tax charge (R1 1,928,281.70) — different formulas on different bases (`:621-624` vs `:780-781`), and neither is ever settled in cash.

### Test 8 — Cross-statement articulation
NI in history rows == NI in diagnostics: **True all rounds.** BS-P&L gross profit vs the engine's CSF-implied gross profit: diverges by −$4.5M (R1) to **−$88.1M (R9) and +$306.9M (R10)** — the two statements measure "the same" revenue at different points of a pipeline that keeps mutating `revenue_base`. Depreciation appears in no cash-flow reconciliation because no indirect-method statement exists.

### Test 9/10 — Equity components & opening position
Share capital and other reserves static at $30M/$5M (no issuance mechanic). Opening BS balances exactly (§2.5).

### Rounding, units, materiality
All lines rounded to cents at each step; identity and subtotal residuals 0.00 throughout; no accumulation observed over 20 rounds. Everything is in whole USD (no thousands scaling) in the backend; frontend display units **not verified**. Materiality threshold applied in this audit: $1 for mechanical ties (they all pass at $0.00), $100K for economic articulations (they fail by millions, so the threshold is academic).

---

## 4. Findings

Labels: **VERIFIED** = read the code and executed a demonstrating test; **READ** = read the code, not executed; **INFERRED** = reasoned from evidence. Confidence High/Medium/Low as defined in the brief.

### ERRORS

**E1 — Retained earnings is a plug; every unmatched movement lands in equity unseen.** `balance_sheet.py:823-841, 840, 905`; `balance_sheet_balanced=True` hard-coded at `:844`. Measured absorption −$12.0M…+$333.5M/round (Test 2). Even accepting the hybrid architecture, reporting "balanced ✓, imbalance 0.0" is incorrect on its own terms — the imbalance was defined away, not eliminated. **VERIFIED, High.**

**E2 — CAPEX acquires assets without cash or debt.** Treasury update is `opening + CSF − interest` (`engine.py:2678`); CAPEX principal is deducted nowhere (searched all treasury writes, listed in §2.2); the "loan" for CAPEX above 20% of treasury exists only as one round's interest charge (`:2661-2672`) — principal never recorded (revolver static, Test 5), never repaid (no mechanic, §2.3). The BS then capitalises 60% of that CAPEX into PP&E (`balance_sheet.py:577-581`). Assets are conjured; the plug books the phantom financing as equity. Under any framework this is wrong. **VERIFIED, High.**

**E3 — Dividends: equity records the requested amount, cash pays the clamped amount.** Engine clamps to available treasury (`engine.py:2593-2594`) and only writes `events["dividends_paid"]` when clamped (`:2607-2610`); the router then **overwrites it with the requested amount** (`router.py:2544`) before the BS engine reads it. Executed: requested $30M against $2M treasury → cash paid $2,000,000; balance-sheet history records dividends **$30,000,000** (Edge 1). The equity bridge and the "retained_earnings_movement" line shown in diagnostics are wrong in every clamped round. **VERIFIED, High.**

**E4 — Goodwill impairment never touches the income statement.** Impairment reduces the asset (`balance_sheet.py:700-703`) but `taxable_income` (`:780`) contains only gross − interest − depreciation − capex_expensed. Executed: R4 goodwill −$2,701,476.62 with no P&L line; absorbed by the plug (bridge, §3). Contradicts IAS 36 (impairment is P&L) — and the module claims IAS 36. **VERIFIED, High.**

**E5 — Brand "revaluation" of an internally generated intangible, direct to equity.** Brand swings ±$10M+/round with reputation/SLO (`:270-303, 638-641`), never through P&L. Doubly non-compliant with the module's own IAS 38 position (which it correctly enforces for SLO/reputation capitals two paragraphs away — `:644-652`): internally generated brands may not be recognised at all (IAS 38.63), and revaluation of intangibles requires an active market. Internally inconsistent even as a teaching convention: the model lectures IAS 38 while violating it on the adjacent line. **VERIFIED, High.**

**E6 — Lease liabilities decay 2.5%/round with no cash payment and no P&L charge.** `:742-745` multiplies by 0.975; no corresponding treasury deduction exists (searched); no interest unwinding (IFRS 16 requires interest + payment; here the liability simply evaporates ≈$0.5M/round into equity via the plug — quantified in the bridge, §3). The ROU asset side *is* depreciated through P&L (`:594-600`), so the two halves of the same lease are treated on different bases. **VERIFIED, High.**

**E7 — Tax is expensed but never paid, and the balance-sheet tax line is a third, unrelated number.** P&L tax = 25% of taxable (`:780-781`); treasury never pays tax (CSF `engine.py:396-402` and all treasury writes contain no tax); BS `tax_provisions` = 20%×25%×gross profit (`:621-624`) — R1: charge $1,928,281.70 vs liability $726,533.51, never settled, never rolled. Three tax numbers, no articulation. **VERIFIED, High.**

**E8 — The de-facto cash flow statement is incomplete.** Waterfall closes at `engine.py:3755` before post_tick crisis impacts and BS-engine charges; measured unexplained movement up to $55.4M/round, $161.3M/10 rounds (Test 3). A student reconciling the waterfall to the cash line will fail through no fault of their own — the dangerous "wrong but plausible" case. **VERIFIED, High.**

**E9 — Negative-treasury debt service is charged at the full annual rate per 6-month round.** `debt_service = |treasury| × corporate_cost_of_capital` (`engine.py:3005-3007`) with no /2, in a codebase that halves annual rates elsewhere (`balance_sheet.py:777`, `:82`; sweep interest `:506`). Measured: R9 charge $131.2M. Doubles the intended cost of distress. **VERIFIED (magnitude) / READ (intent), High** that it is inconsistent; whether the un-halved rate is deliberate punishment needs the developer's answer (§10).

### INCONSISTENCIES

**I1 — Five uncoordinated interest regimes.** (1) BS P&L: total debt × ESG-WACC/2 + accretion (`balance_sheet.py:770-778`) — accrual only, never cash; (2) CAPEX loan interest at `loan_interest_rate` un-halved (`engine.py:2670-2672`) — cash only, never P&L; (3) emergency credit at rate+2% (`:2662-2668`); (4) negative-treasury service at cost_of_capital un-halved (`:3005-3007`); (5) sweep revolver interest at loan rate/2 (`balance_sheet.py:504-509`). No student can reconcile "interest expense" across the statements. **VERIFIED (each computed in trace), High.**

**I2 — Cash-timing concepts implemented as permanent revenue destruction.** DSO defers 2–12% of `revenue_base` each round — cash returns next round, but the *revenue baseline* is permanently reduced (`engine.py:2473-2491`); cash-conversion drag multiplies `revenue_base` by 0.88–1.0 *permanently and compoundingly* (`:2496-2501`, "not all revenue becomes available cash" — a collections concept applied to the accrual revenue stock). Measured: group revenue 75M seeded → 65.2M after R1 → 26.0M by R10 (combined with other pressures). The BS receivables line is a *third*, separate DSO model (`balance_sheet.py:613-615`, acknowledged as uncoordinated in the FIX-10 note :606-609). Terminal valuation then grades students on this eroded `revenue_base`. **VERIFIED, High.**

**I3 — "Straight-Line Depreciation" is reducing-balance.** Label at `balance_sheet.py:586`, implementation is 5% of the *evolving* balance; executed 20-round run: PP&E 21.4M → 8.08M, asymptotic, never fully depreciates (Edge 4). Straight-line requires cost/useful-life off a fixed base. A student who checks will find the numbers contradict the label. **VERIFIED, High.**

**I4 — Treasury floor and bailouts inject equity through the plug.** Floor −$500M + ESG relief (`config.py:170`; `engine.py:3015, 3727-3730`); R9 clamp manufactured the +$333.5M RE residual (Test 2). Also: the floor is applied inside process_tick, then BS-engine charges push treasury below it again (R8 close −$418M vs floor −$380M) — the floor doesn't hold at round close, then next round's re-floor creates income from nowhere. **VERIFIED, High.**

**I5 — `events["dividends_paid"]` means "clamped" in the engine and "requested" in the router.** Same key, two semantics (`engine.py:2607-2610` vs `router.py:2544`); root cause of E3 and a latent trap for any future consumer of the key. **READ, High.**

**I6 — Debt definitions differ per metric.** Covenant net debt = revolver + green bonds + short-term debt (`balance_sheet.py:416-420`); D/E = *total liabilities*/equity (`:850`); leases and decommissioning are debt-like but in neither consistently. Each defensible; together incoherent. **READ, Medium.**

**I7 — The two statements disagree on revenue.** BS-P&L gross profit vs engine CSF-implied gross profit diverge up to $306.9M in a round (Test 8) because revenue keeps mutating between the CSF snapshot and the BS snapshot. Both claim to describe the same round. **VERIFIED, High.**

**I8 — The balance-sheet engine is fail-silent.** `round_logic.py:622-678`: any exception → `print("[WARN] Balance sheet engine failed")`, game continues, statement silently freezes at last round's values. In a classroom the frozen statement would be indistinguishable from a real one. **READ, High.**

**I9 — The module header cites `balance_sheet_critique.md` (`balance_sheet.py:31`), which does not exist in the repo.** Verified against the full file listing. The provenance of FIX-1…13 is unauditable. **VERIFIED, Medium.**

### SIMPLIFICATION — UNSAFE

**U1 — "balance_sheet_balanced: True / imbalance: 0.0" as a hard-coded diagnostic** (`:844-845`). Teaches that "it balances" is evidence of integrity. It must either compute a real articulation check (the §8 invariants) or be removed. Minimum fix: report the Test-2 residual as `unexplained_equity_movement`. **VERIFIED, High.**

**U2 — Tax asymmetry with no loss carry-forward and no cash/payable articulation** (`:780-781` `max(0,…)`; nothing rolls). A student learns tax is a P&L decoration. Minimum fix: either pay the charge from treasury (one line in the tick) and carry the payable, or annotate the statement "tax is notional in this simulation". Under generic teaching conventions the *no-carry-forward* half alone would be a SAFE simplification if stated; the zero-articulation half is not. **VERIFIED, High.**

**U3 — Dividends with negative retained earnings and negative equity pass without comment.** Only the cash clamp exists (`engine.py:2593-2594`); executed: $5M dividend recorded while RE = −$40.6M (Edge 6). Teaches that distributable reserves are not a constraint — something a later corporate-law or accounting course must untrain. Minimum fix: block (or flag on the face of the statement) dividends when RE < 0. **VERIFIED, High.**

**U4 — D/E = 99.0 sentinel when equity ≤ 0** (`balance_sheet.py:851-852`; from R6 the run shows literal 99.0). A magic number shown as if it were a ratio. Fix: null + "n/m — negative equity" label. **VERIFIED, Medium.**

**U5 — Debt that never moves.** The revolver sits at $50M for the whole game regardless of borrowing, repayment is impossible, and all real financing stress surfaces as swept "short-term debt". Executive students will internalise a balance sheet where financing decisions have no balance-sheet consequence. (The sweep itself is fine — see S3 — the missing drawdown/repayment mechanic is the unsafe part, and it is the same hole as E2.) **VERIFIED, High.**

**U6 — A team that submits nothing still earns full gross profit** (Edge 3: NI +$5.9M, treasury +$11.0M). Defensible as "the business runs itself for a period"; unsafe if unstated, because the no-show team can outperform an active one. Document or penalise. **VERIFIED, Medium.**

### SIMPLIFICATION — SAFE (document for instructors)

**S1 — ESG capitals off-BS with IAS 38 note + scholarly on-BS toggle** (`:234-246, 654-684`). Genuinely good pedagogy; the toggle's self-absorption via the closing identity is honest *given* the plug. Document that toggling changes RE by construction.
**S2 — Terminal-value EBITDA floor at 0 with raw value disclosed** (`terminal_valuation.py:469-489`). Documented, transparent, defensible.
**S3 — Negative-cash sweep to short-term debt, priced** (`balance_sheet.py:480-509`). Correct presentation instinct; SET-not-accumulate is right given per-tick re-derivation. Keep; document that the engine's treasury remains the cash truth.
**S4 — Working-capital proxy formulas** (60-day inventory, DSO/DPO factors). Fine *as labelled proxies*; today nothing labels them (see P1/P6).
**S5 — No deferred tax, no FX on the BS, no NCI, single entity.** Appropriate for level; state it in the instructor notes.
**S6 — Goodwill impairment every 2nd round = annual testing** at 6-month cadence (`:686-689`). Internally consistent; the *P&L bypass* is the error (E4), not the cadence.
**S7 — Covenant machinery** (net debt/EBITDA, ESG-WACC tightening, cure-period ladder, `:393-473`) — internally coherent and pedagogically rich. FIX-4's true-EBITDA addback is correct.
**S8 — Dividend cash clamp (VULN-001)** — right guard; the *reporting* is the bug (E3).

### PRESENTATION

**P1 — Inventory sits in `tangible_assets` (a non-current grouping) on an "IAS 1 format" statement** (`:196-200`). Inventory is a current asset; any textbook current-ratio exercise against this statement mis-computes. **VERIFIED, High.**
**P2 — No current/non-current split of debt or leases; no current-portion migration as maturities approach; revolver labelled non-current.** READ, Medium.
**P3 — Prepayments frozen at seed value forever** (`:147` only write). READ, Medium.
**P4 — "Tax provisions: quarterly prepayment (~20% of annual)"** comment in a 6-month-round model (`:621`) — muddled period language on top of E7. READ, Low-stakes.
**P5 — `covenant_trigger_ratio` default 3.5 lives in the BS dict and is overridden by difficulty tier** (`round_logic.py:629-636`) — fine, but the statement face shows no indication that the covenant threshold varies by difficulty. READ, Low.
**P6 — No statement labels the working-capital lines as model proxies**, and the income statement exists only as a diagnostics dict — whether players ever see a coherent P&L depends on the frontend, which I could not verify (§9).

---

## 5. Edge-case results (Phase 3) — all executed

| Scenario | What happened (measured) | Classification |
|---|---|---|
| Loss-making round | NI −$12.0M (R2) etc.; statements produced | Correct-looking, but articulation errors as above |
| Consecutive losses (R2–R10) | Runs; RE plug tracks net assets | Wrong-but-plausible (residuals hidden) |
| Negative retained earnings (R5+) | No flag, no guard; dividends still recordable (Edge 6) | **Wrong-but-plausible** |
| Negative total equity (R6+, −$64M → −$396M) | D/E snaps to literal 99.0; covenant already "breached"; game continues | Visible-ish (sentinel), otherwise plausible |
| Cash → 0 → negative | BS cash floors at 0, deficit swept to short-term debt to the cent; treasury keeps true negative | **Correct** (best-behaved mechanism in the model) |
| Dividends > cash ($30M vs $2M) | Cash pays $2M; **equity records $30M** | **Wrong-but-plausible — the worst kind** |
| Dividends > retained earnings | No guard; recorded in full | Wrong-but-plausible |
| Inventory → 0 with demand | Impossible by construction (inventory = f(OPEX)); zero only if OPEX = 0 | N/A — document |
| Excess inventory | Impossible by construction (no stock accumulation mechanic) | N/A — document |
| Asset fully depreciated | Never happens: reducing balance is asymptotic (20 rounds: 21.4M→8.08M, never ≤0) | Correct arithmetic, contradicts "straight-line" label (I3) |
| Debt repayment > balance | **No repayment mechanic exists at all** | N/A — the gap is the finding (E2/U5) |
| Zero revenue round | Statement produced; AR 0, inventory unchanged (OPEX-driven), NI −$57.8M; treasury −$6.7M | Correct-looking; plausible |
| Team submits nothing | Runs cleanly; **full gross profit still earned**, NI +$5.9M, treasury +$11.0M; BS balances | Wrong-but-plausible (U6) |
| Extreme decisions (capex 2× treasury) | Capped at 2× treasury (`engine.py:2649`); only interest charged; no cash out (E2) | Wrong-but-plausible |
| All teams identical decisions | Sessions are independent state machines; no cross-team financial coupling found in the commit path | N/A (READ, Medium — multiplayer surface not fully audited) |
| Insolvency | Thresholds fire (austerity flags at −$100M; bailout via distress detection; treasury floor −$380M with ESG relief); **floor doesn't hold after post-tick charges (R8: −$418M), next round's re-floor mints equity (+$333.5M residual)** | **Wrong-but-plausible** |
| Final round (R10) | Terminal EBITDA computed on eroded `revenue_base` (I2); negative EBITDA floored at 0 with raw value disclosed | Documented simplification (S2); grading dependency on I2 noted |

---

## 6. Pedagogical assessment (Phase 4) — professor's hat

**Traceability.** The waterfall with `because`/`counterfactual` strings is the best teaching artefact in the engine — a student can trace CSF, loan interest, carbon fees to decisions. But the *balance sheet* is not traceable: the single most instructive question an instructor can ask ("your equity moved $14M but you lost $12M — where did $26M come from?") currently has no answer on any statement, because the plug ate it. The statements are, in the brief's phrase, a scoreboard, not a teaching instrument — with one exception: the covenant/sweep machinery genuinely teaches.

**Level fit.** Line-item granularity (ROU assets, decommissioning accretion, green bonds, stranded-asset disclosure) is right for exec/MBA — recognisable and rich without being a chart of accounts. The problem is not detail, it is articulation.

**Ratio support.** Current ratio: broken by P1 (inventory misplaced) — the components exist but are mis-grouped. Net debt/EBITDA: supported and internally consistent. D/E: sentinel 99.0 breaks it in exactly the rounds where leverage discussion is most interesting (U4). ROE/ROA: computable but poisoned by the plug (equity) and phantom assets (E2). Interest cover: impossible — five interest regimes (I1).

**What must later be untaught** (the unsafe list, ranked by damage): (1) assets can be acquired without cash or financing (E2); (2) "the balance sheet balances" as self-evident proof of integrity (E1/U1); (3) dividends constrained only by cash, not by distributable reserves (U3); (4) impairment and revaluations that skip the P&L (E4/E5); (5) tax as a notional decoration (E7/U2).

**Highest teaching value per unit of modelling cost:** (a) an "Other equity movements" note that itemises exactly what the plug currently hides — the re_bridge.py decomposition *is* that note, and it closes to the cent; (b) route impairment through the P&L (one line moves); (c) pay the tax charge from treasury (one line); (d) fix the dividends amount (one word: pass the clamped figure); (e) label depreciation honestly (one string). Items (b)–(e) are single-line changes with outsized pedagogical return.

---

## 7. Remediation plan (Phase 5)

Constraints respected: round mechanics, decision inputs and session flow untouched; all changes confined to the financial computation/presentation layer. ⚠️ = CHANGES RESULTS, with magnitude and migration note. Efforts: S < ½ day, M ≈ 1–2 days, L ≈ 1 wk+.

**Safety net first (do before any fix):** the repo already has the right instrument — `tests/test_financial_golden_trace.py` with its documented rebaseline protocol. Extend it with the §8 invariants as permanent per-round assertions, and pin one golden statement snapshot per round (the BS history rows already carry `full_statement` deep copies — `balance_sheet.py:915-941` — so the storage format exists). If nothing else from this audit ships, ship that.

### Ranked findings table

| # | Finding | Category | Conf. | Evidence (file:line + test) | Fix | ⚠️ | Effort |
|---|---|---|---|---|---|---|---|
| 1 | RE is a plug; residuals ±$0.4M–$333.5M/round | ERROR | High | balance_sheet.py:840,905; Test 2 | Phase A: report `unexplained_equity_movement` (= Test-2 residual) on the statement + itemised "Other equity movements" note (bridge decomposition). Phase B: true RE roll-forward (RE += NI − div ± itemised other movements), with a *visible* imbalance line if it ever fails | Phase A no; Phase B ⚠️ RE re-stated by cumulative residuals (tens of $M by mid-game); scoring unaffected if scores don't read RE (they read treasury/M_R — verified in terminal path) | A: S · B: L |
| 2 | CAPEX: no cash out, no debt, no repayment | ERROR | High | engine.py:2678, 2661-2672; Test 5; Edge capex-2× | Book CAPEX cash: treasury −= capex up to free limit; excess draws a `capex_loans` liability line; add amortising repayment (e.g. 10%/round) + interest on outstanding balance; retire the one-shot interest hack | ⚠️ **Large** — solvency band shifts for every script (the golden-trace calibration note already shows the band is narrow); requires retuning free_csf_pct / floors; version the model | L |
| 3 | Dividends recorded at requested, paid at clamped | ERROR | High | router.py:2544; engine.py:2607-2610; Edge 1 | Router: pass `events.get("last_dividends_paid", body.dividends_paid)` (engine sets it to the clamped figure unconditionally at :2604); rename key or split `dividends_requested`/`dividends_paid` | ⚠️ only in clamped rounds (RE + history rows); historical runs: pin to old model version | S |
| 4 | Goodwill impairment bypasses P&L | ERROR | High | balance_sheet.py:700-703 vs :780; bridge R4 | Add impairment to the P&L between depreciation and interest; keep tax base definition explicit | ⚠️ NI lower in impairment rounds (−$1–3M typical); RE unchanged once #1 Phase B lands | S |
| 5 | Brand reval direct-to-equity on an internally generated intangible | ERROR | High | :270-303, 638-641; bridge R2/R4 | Either freeze brand at base (IAS 38-clean) and move the rep/SLO-driven value next to the ESG capitals as a disclosure, or route revaluation through P&L as "brand impairment/(recovery)" with a big label | ⚠️ total assets −(brand−base); moderate | M |
| 6 | Lease liability decays with no P&L/cash | ERROR | High | :742-745; bridge (≈$0.5M/rnd) | Model a lease payment: treasury −= payment; liability −= (payment − interest); interest → P&L. Or drop the IFRS 16 claim and freeze both sides | ⚠️ small-moderate | M |
| 7 | Tax never paid; BS tax line unrelated to charge | ERROR | High | :780-781, 621-624; engine treasury writes | treasury −= tax_charge (or accrue payable settled next round); make `tax_provisions` = unpaid balance; add carry-forward or document asymmetry | ⚠️ treasury lower in profitable rounds ($1–2M/round early) | M |
| 8 | Waterfall misses post-tick & BS-engine cash moves | ERROR | High | engine.py:3755; Test 3 drift ≤$55.4M/rnd | Emit waterfall entries from post_tick and the BS engine (sweep interest, covenant surcharge already produce diagnostics — append them); assert closure (§8 inv. 3) | No | M |
| 9 | Negative-treasury interest not halved for 6-mo round | ERROR | High | engine.py:3005-3007; R9 $131M | `× corporate_cost_of_capital / 2` (if the doubling was intended as a distress premium, name it as one) | ⚠️ distressed runs materially better off | S |
| 10 | Five interest regimes | INCONSISTENCY | High | I1 citations | Unify on ESG-WACC (already the covenant/BS rate); every cash interest also lands one P&L line | ⚠️ moderate | M |
| 11 | Cash-timing implemented as permanent revenue destruction | INCONSISTENCY | High | engine.py:2473-2501; rev 75M→26M | Make DSO/conversion pure timing: defer cash, leave `revenue_base` (accrual) intact; drag becomes a receivables/bad-debt cost line | ⚠️ **Large** — raises revenue trajectory for everyone; re-calibrate difficulty; version | L |
| 12 | "Straight-line" is reducing balance | INCONSISTENCY | High | :586-592; Edge 4 | Rename to reducing-balance (S) or implement SL off gross cost with accumulated depreciation (M) | Rename: no | S/M |
| 13 | Treasury floor mints equity; floor doesn't hold at close | INCONSISTENCY | High | engine.py:3015,3727; Test 2 R9 | Apply floor once, after all charges incl. BS engine; book the clamp explicitly as "emergency creditor support" (waterfall + equity note) | ⚠️ deep-distress runs | M |
| 14 | `dividends_paid` key double meaning | INCONSISTENCY | High | I5 | Split keys (part of #3) | with #3 | S |
| 15 | Debt metric definitions differ | INCONSISTENCY | Med | I6 | Define net debt once (incl./excl. leases — pick and label); reuse for D/E numerator note | No | S |
| 16 | Statements disagree on revenue (≤$307M) | INCONSISTENCY | High | Test 8 | Snapshot revenue/opex once per round (post-pipeline) and feed both CSF reporting and BS P&L from it | ⚠️ waterfall labels | M |
| 17 | BS engine fail-silent | INCONSISTENCY | High | round_logic.py:678 | Keep the try/except, but surface a visible "statement unavailable this round" flag to UI + structured log | No | S |
| 18 | `balanced=True` hard-coded | UNSAFE SIMPL. | High | :844-845 | Replace with computed residual (inv. 2) | No | S |
| 19 | Dividends vs negative RE unguarded | UNSAFE SIMPL. | High | Edge 6 | Block or face-of-statement warning | ⚠️ behavioural only | S |
| 20 | D/E 99.0 sentinel | UNSAFE SIMPL. | Med | :851-852 | null + "n/m (negative equity)" | No | S |
| 21 | No-show team earns full profit | UNSAFE SIMPL. | Med | Edge 3 | Document, or apply a drift penalty | ⚠️ if penalised | S |
| 22 | Inventory in non-current group | PRESENTATION | High | :196-200 | Move to current_assets (pure re-grouping; totals unchanged) | No (ratios change) | S |
| 23 | No current-portion split; static prepayments; "quarterly" comment | PRESENTATION | Med | P2-P4 | Label/fix opportunistically | No | S |
| 24 | Missing `balance_sheet_critique.md` | INCONSISTENCY | Med | listing | Restore or delete the reference; keep FIX provenance in-repo | No | S |

### Grouped

* **Correct before the next cohort:** #3 (one-line, wrong equity numbers in clamped rounds), #4 (one-line), #9 (one-line), #17, #18, #1 Phase A, #22 — all S-effort, and only #3/#4/#9 change any number. Plus: land the §8 invariants + golden snapshots.
* **Correct this term:** #6, #7, #8, #10, #12, #13, #16, #19, #20 — the articulation layer.
* **Improve when convenient:** #2 and #11 (the two big ⚠️ re-calibration items — do them together behind a model version, because both move the solvency band), #5, #15, #21, #23, #24, #1 Phase B.
* **Document rather than change (instructor notes):** S1–S8 (§4), the inventory/OPEX proxy, no-repayment-by-design *if* #2 is deferred, no deferred tax/FX/NCI, the no-show behaviour until decided, the difficulty-tier covenant trigger.

### Versioning / historical runs

Add `FINANCIAL_MODEL_VERSION = "2.0.0"` to `config.py`, stamp it into `global_state` at session creation, and have `run_new_engines` dispatch on it (the BS engine is already toggle-gated, so a version gate is idiomatic here). Pin all pre-fix sessions to `"1.x"` behaviour; the golden-trace rebaseline protocol (`MURESSONS_REBASELINE_GOLDEN=1`, same-commit diff rule) already enforces that every number-moving change is reviewed with its diff. For #2/#11, cut the version *once* with both included — two separate recalibrations would double the migration cost.

---

## 8. Permanent invariant assertions — as code

Drop-in: `backend/financial_invariants.py` + call from `process_balance_sheet_tick` (dev/CI: raise; prod: log + surface). Invariants 1, 3, 4, 5 pass today; **2, 6, 7 fail today** — they are the fix acceptance criteria and should enter CI as `xfail(strict=True)` until their fixes land, so the day they pass is noticed.

```python
"""financial_invariants.py — articulation assertions for the Muressons engine.
Call check_all(...) at the end of process_balance_sheet_tick (dev: raise, prod: log).
TOL_ABS is cents-level for mechanical ties; TOL_ECON for economic bridges."""

TOL_ABS  = 0.01          # mechanical arithmetic must tie to the cent
TOL_ECON = 1.00          # accumulated float rounding across a bridge

class FinancialInvariantError(AssertionError):
    pass

def _sections(bs):
    a = (sum(bs["tangible_assets"].values()) + sum(bs["intangible_assets"].values())
         + sum(bs["current_assets"].values()))
    l = (sum(bs["non_current_liabilities"].values()) + sum(bs["current_liabilities"].values()))
    e = bs["share_capital"] + bs["other_reserves"] + bs["retained_earnings"]
    return a, l, e

def inv1_identity_independent(bs):
    """A = L + E recomputed from raw line items — NOT from the stored totals,
    and NOT trusting the RE derivation: uses the stored RE figure as data."""
    a, l, e = _sections(bs)
    if abs(a - l - e) > TOL_ABS:
        raise FinancialInvariantError(f"A-L-E residual {a-l-e:.2f}")
    if abs(a - bs["total_assets"]) > TOL_ABS or abs(l - bs["total_liabilities"]) > TOL_ABS:
        raise FinancialInvariantError("stored totals drifted from line-item sums")

def inv2_re_rollforward(bs_open, bs_close, net_income, dividends_paid_cash,
                        other_equity_movements=0.0):
    """RE_open + NI - dividends(CASH-effective) + itemised other movements = RE_close.
    other_equity_movements must be an itemised, disclosed number — not a residual.
    FAILS TODAY (plug): keep as xfail(strict=True) until remediation #1 Phase B."""
    expected = bs_open["retained_earnings"] + net_income - dividends_paid_cash + other_equity_movements
    resid = bs_close["retained_earnings"] - expected
    if abs(resid) > TOL_ECON:
        raise FinancialInvariantError(f"RE bridge residual {resid:,.2f}")

def inv3_cash_articulation(bs, corporate_treasury):
    """BS cash == max(0, treasury); swept deficit == -min(0, treasury)."""
    cash = bs["current_assets"]["cash_and_equivalents"]
    std  = bs["current_liabilities"]["short_term_debt"]
    if abs(cash - max(0.0, corporate_treasury)) > TOL_ABS:
        raise FinancialInvariantError(f"cash {cash:,.2f} != max(0, treasury {corporate_treasury:,.2f})")
    if abs(std - max(0.0, -corporate_treasury)) > TOL_ABS:
        raise FinancialInvariantError(f"short_term_debt {std:,.2f} != swept deficit")

def inv4_ppe_rollforward(ppe_open, capex_capitalised, depreciation_ppe, ppe_close):
    resid = ppe_close - (ppe_open + capex_capitalised - depreciation_ppe)
    if abs(resid) > TOL_ABS:
        raise FinancialInvariantError(f"PP&E roll residual {resid:.2f}")

def inv5_income_statement_arithmetic(inc):
    gp = inc["revenue"] - inc["opex"]
    taxable = gp - inc["interest_expense"] - inc["depreciation"] - inc["capex_expensed"]
    if abs(gp - inc["gross_profit"]) > TOL_ABS or abs(taxable - inc["taxable_income"]) > TOL_ABS:
        raise FinancialInvariantError("P&L internal arithmetic broken")
    if abs((inc["taxable_income"] - inc["tax_charge"]) - inc["net_income"]) > TOL_ABS:
        raise FinancialInvariantError("NI != taxable - tax")

def inv6_waterfall_closure(waterfall, treasury_open, treasury_close):
    """The cash statement must explain the whole round: initial + Σentries = close.
    FAILS TODAY by up to $55M/round: xfail until remediation #8."""
    explained = waterfall["initial_treasury"] + sum(e["amount"] for e in waterfall["entries"])
    resid = treasury_close - explained
    if abs(resid) > TOL_ECON:
        raise FinancialInvariantError(f"waterfall unexplained cash {resid:,.2f}")

def inv7_dividends_consistency(recorded_equity_distribution, cash_dividends_paid):
    """The equity distribution recorded on the statement equals the cash that left.
    FAILS TODAY in clamped rounds: xfail until remediation #3."""
    if abs(recorded_equity_distribution - cash_dividends_paid) > TOL_ABS:
        raise FinancialInvariantError(
            f"dividends: equity says {recorded_equity_distribution:,.2f}, "
            f"cash paid {cash_dividends_paid:,.2f}")

def check_all(bs_open, bs_close, gs, diagnostics, waterfall=None):
    inc = diagnostics["income_statement"]
    inv1_identity_independent(bs_close)
    inv3_cash_articulation(bs_close, gs.get("corporate_treasury", 0.0))
    if bs_open is not None:
        inv4_ppe_rollforward(
            bs_open["tangible_assets"]["property_plant_equipment"],
            diagnostics["capex_capitalised"],
            round(bs_open["tangible_assets"]["property_plant_equipment"] * 0.05, 2),
            bs_close["tangible_assets"]["property_plant_equipment"])
    inv5_income_statement_arithmetic(inc)
    # xfail-until-fixed set:
    # inv2_re_rollforward(...); inv6_waterfall_closure(...); inv7_dividends_consistency(...)
```

Plus one CI test that runs the golden-trace harness for 10 rounds calling `check_all` every round — that converts every invariant into a per-round regression tripwire with zero new infrastructure.

---

## 9. What I could not verify — and what closes each gap

1. **The player-facing rendering** (labels, units, ordering, whether the P&L diagnostics are shown at all): frontend was not staged into the audit environment. *Close by:* staging `frontend/` (the components that consume `/balance-sheet`) and re-running the presentation review. My P-findings are backend-shape only.
2. **Production-exact residual magnitudes:** my harness omits the router's pillar-aggregation deltas and crisis-severity derivation (same omission the repo's own golden trace documents). Mechanisms and directions are code-verified; sizes in a live cohort will differ. *Close by:* one instrumented live commit with `check_all` logging.
3. **Multiplayer coupling:** I read no cross-session financial state in the commit path, but did not audit the full multiplayer/negotiation surface (`negotiation.py`, coordination stores). "All teams identical" therefore rated N/A at Medium confidence only.
4. **Postgres vs in-memory parity** for BS state round-trips (`test_postgres_parity.py` exists; not executed here — no Postgres in the audit environment).
5. **Green-bond issuance path end-to-end** (`:737-740` is READ only — no round in my scripts issued one). *Close by:* a scripted R3 Scope-3 decision run.
6. **Side-track financial bridges** (`side_tracks/bridge_schemas.py`) and extended-horizon (R11–20) *via the router* (I ran the engine loop directly).
7. **`balance_sheet_critique.md`** — cited, absent; the reasoning behind FIX-1…13 could not be checked against its source.
8. **Whether E9's un-halved rate is intentional** distress pricing — the code comment is silent.

An honest note on the repo's own tests: the suite is unusually serious (golden traces, integrity suites, treasury waterfall tests), but **no test in `backend/tests/` asserts the A=L+E identity or any roll-forward** — understandable, since the plug makes the identity untestable-by-construction. The §8 invariants are the missing class.

## 10. What I need from you — answers that would change verdicts

1. **Is the "financing-by-assumption" CAPEX model (E2) a deliberate design** ("capex is auto-loan-financed off-screen")? If yes, E2 reclassifies from ERROR to UNSAFE SIMPLIFICATION — the fix then is a disclosed `capex_loans` liability line rather than a cash rework, which is much cheaper (#2 drops from L to M).
2. **Is the un-halved negative-treasury rate (E9) an intended distress premium?** If yes: relabel and document; if no: halve it. Changes verdict wording only, but changes the fix.
3. **Do any scoring/grading paths read `retained_earnings`, `net_assets` or `debt_to_equity`?** I traced terminal valuation to treasury/M_R/BU state and found no RE dependence, but a definitive answer decides whether remediation #1 Phase B is ⚠️ for rankings or cosmetic.
4. **Which statements do players actually see** (BS only? P&L? waterfall?) — determines how much of the articulation layer is student-visible vs instructor-only, and re-ranks #8 vs #4-#7.
5. **Is the permanent revenue erosion (I2) intended difficulty tuning?** If yes it should be renamed (it is not "DSO"/"cash conversion"); if no, #11 is a calibration-critical bug.
6. ~~Confirm the intended framework~~ — **Answered during the audit: IFRS.** Consequence: the framework violations (E4, E5, E6, E7, P1) are now hard remediation requirements, not labelling choices. Until #4-#7 and #22 land, instructor materials should describe the statements as "IFRS-format, with the following known departures" and list them — the sharp student will find each one.

---
*Method note: every number in this report was produced by executed code in `audit/` (`run_trace.py`, `recon.py`, `re_bridge.py`, `edges.py`) against the staged repo snapshot of 2026-08-04; every code claim carries a file:line citation to that snapshot. Findings labelled READ were not executed; findings labelled INFERRED are marked as such (there are two: multiplayer N/A rating, and the R9 clamp attribution which is VERIFIED numerically but INFERRED causally).*
