# Muressons — Redundant-File Review & Archive Plan

*Review only — no files have been moved. Every candidate below was checked
against the live import graph, runtime loaders, the pytest suite, the
production build, and the player smoke before being classified. The plan
executes in phases, each with the same gate battery as every code phase in
this engagement, using `git mv` so history is preserved and any phase can be
reverted with one command.*

---

## 1. How "redundant" was decided

A file is a candidate only if ALL of these hold: (a) nothing in `backend/`
imports it and no runtime loader globs it; (b) no frontend file imports it
(static `from`, `require`, or `next/dynamic import()` — all three scanned);
(c) the pytest suite (`backend/tests/`, 976 green) does not touch it;
(d) the production build does not consume it; (e) it is not live state the
app writes at runtime. Anything referenced by the safety/ops documents
(`SAFETY_MANIFEST`, `DEPENDENCY_MAP`) stays.

## 2. PROTECTED — looks redundant, is not (do not archive, ever)

| Path | Why it must stay |
|---|---|
| `backend/db/materiality_config_*.json` (11 files) | Runtime-loaded by `materiality_db.py` (`BU_CONFIG_FILES` builds paths from these names) |
| `backend/db/industry_configs/*`, `industry_master_materiality.xlsx`, `upload_templates/` | Your new per-industry pipeline; served by the config endpoints |
| `backend/db/pillar_overrides_*.json`, `stakeholder_config_*.json` | Runtime loaders (pillar + regional stakeholder systems) |
| `excel_templates/*.xlsx` (16) | Authoring templates for the Excel upload pipeline |
| `simulation_config.json` / `.provenance.json` / `.xlsx` | Read by `config_excel.py` + `admin_router.py` |
| `sessions.json`, `db/admin_audit.jsonl`, `backend/db/muressons_state.db` | Live runtime state (better gitignored than archived — see §6) |
| `guide_images/` (17) | Consumed by the doc generators when manuals are rebuilt |
| `revert.py` | Referenced by SAFETY_MANIFEST / DEPENDENCY_MAP as a recovery tool |
| Root `REVIEW_*.md`, playbooks, `SIMULATION_CONTEXT.md`, `blueprint.md`, `README.md` | Current project documentation |
| `db/init.sql`, `db/seed_round1.*` | Postgres path (`USE_MEMORY_DB=false`) seeds |

## 3. ARCHIVE CANDIDATES — by phase

### Phase AR1 — zero-risk leftovers (33 files, no references anywhere) ✅ executed (`0b5d894`)
- Root: `test.bat`, `test_sub.docx`, `clean_frontend_sdg.js` (one-shot codemod, already applied)
- `scratch/` (4): `fix_lock.py`, `generate_syllabus_docx.py`, `test_ceo_interview.py`, `test_lifespan.py`
- `reports/` (23): traversal reports + facilitator evidence from the May test campaign — historical evidence, not consumed by anything
- `db/` snapshots (3): `facilitator_registry.json.bak`, `facilitator_registry.json.before_cleanup`, `memory_snapshot.json.before_cleanup`

### Phase AR2 — backend manual test harnesses (21 files)
`backend/test_*.py` at backend root (`test_deep_audit`, `test_e2e_multiplayer`,
`test_hc_comprehensive`, `test_all_pathways_x_paradigms`, …). These are
manual/e2e diagnostic scripts that need a live server; the real suite lives in
`backend/tests/` (30 files, 976 green) and does not import them. The player
smoke runs from git blob `e2905f0`, so moving files cannot affect it.
*Caveat:* they are genuinely useful diagnostics — archiving keeps them
runnable from the archive folder (they're standalone), but you may prefer
`backend/manual_tests/` instead of the archive. **Your call — see question 2.**

### Phase AR3 — orphaned frontend components (17 files, ~4,900 lines)
No import of any kind found in the 201-file frontend source graph:

`CapitalGauges` (132) · `CohortDiversityPanel` (239) · `ConsequenceReplay` (401) ·
`DecisionModal` (331) · `DecisionParadigmConfig` (1065) · `DecisionPressureTimer` (173) ·
`ExecutiveMailbox` (349) · `FinalReport` (506) · `GlobalSettings` (105) ·
`HelpTooltip` (55) · `InductPlayerModal` (208) · `IndustryBenchmarkPanel` (188) ·
`LivingPlanet` (272) · `ScenarioPresets` (128) · `StakeholderSentimentPanel` (173) ·
`StrategicPillarsWorkspace` (284) · `utils/format.js` (49)

These read like superseded ancestors of current components (`ExecutiveMailbox`
→ mailbox tab in ExecutiveCockpit; `FinalReport` → GameOverSummary;
`DecisionModal` → Decision Canvas). Their orphaned `.module.css` siblings move
with them. The gate for this phase is the strongest: a full production build
from the moved tree — if the build or any route breaks, the file was not an
orphan and comes straight back.

### Phase AR4 — documentation duplicates + generator relocation (judgment)
- `docs/` (47 files): keep the highest version of each family (e.g.
  `Facilitator_Manual_v10`), archive lower versions that survived the earlier
  cleanup. Exact list produced during the phase, shown before moving.
- Root doc generators `gen_context_docx.py` (147 KB) and
  `gen_student_manual_v10.py` (94 KB): current-generation tools, not
  redundant — but they don't belong at repo root. Proposal: relocate to
  `scripts/docgen/` (not archive). **Your call — see question 3.**

## 4. Execution rules (every phase)

1. `git mv` only — history preserved; rollback = `git revert <phase-commit>`.
2. Destination: single archive root with subfolders
   (`<archive>/scripts_legacy/`, `/backend_manual_tests/`,
   `/frontend_retired/`, `/reports/`, `/db_snapshots/`, `/docs_superseded/`).
3. One commit per phase with the file list in the message.
4. Gate battery after each phase: reference re-scan of the moved names →
   pytest (976) → jest (56) → ESLint → full production build → unmodified
   player smoke. A failure reverts the phase, not the gate.
5. `backend/`, `frontend/app` live code, and all §2 protected paths are
   untouchable throughout.

## 5. Decisions (RESOLVED — all phases executed)

1. **Archive location** — ✅ renamed `temp_archive/` → `archive/` (AR0,
   `2d7a6c7`); everything consolidated there.
2. **Backend manual harnesses** — ✅ archived to
   `archive/backend_manual_tests/` (AR2 `99f209c` relocated, then AR2b
   `0766c93` archived per review decision); README documents how to run
   them from the archive.
3. **Doc generators** — ✅ relocated to `scripts/docgen/` (AR4b, `f7a593d`).
4. **docs/ duplicate pass (AR4a)** — ✅ `Muressons_Student_Manual_v9.docx`
   archived to `archive/docs_superseded/` (`e3db6e0`). docs/ now holds a
   single current version of every document.

### AR3 orphan verification (second pass, on request)

Beyond the three-form import scan (static `from`, `require`,
`next/dynamic import()`), a second sweep confirmed: (a) **zero word-boundary
textual references** of any kind to 15 of the 17 names anywhere in live
frontend source; (b) the four textual hits are all benign —
`CFOOverrideModal` imports only `DecisionModal.module.css` (which stayed in
place for exactly this reason), and the other three are comments, two of
which read "merged from GlobalSettings / ScenarioPresets", i.e. the orphans
are pre-merge ancestors of live components; (c) **no variable-path dynamic
imports exist anywhere** in the app — every `import()` uses a literal path,
so nothing can load these files by constructed string; (d) the production
build from the post-move tree compiled green and **prerendered all 10
routes** (static generation executes every page component), and jest passed
56/56. Moving them cannot affect simulation flow or logic: they were
unreachable code.

## 6. Non-archive housekeeping (DONE where marked)

- ✅ `.claude/skills/frontend-design/` (corrupted, I/O errors) deleted from
  disk. Reinstall the skill via Settings if you still want it.
- ✅ Runtime state untracked (`952bdb6`): `db/admin_audit.jsonl` and
  `backend/db/muressons_state.db` removed from the index (worktree copies
  untouched); `.gitignore` now covers them plus `sessions.json` (which was
  already untracked).
- Root `package.json` declares only `puppeteer` with a 11 KB lockfile and a
  root `node_modules/` — if no script drives puppeteer anymore, this trio is
  an AR1-class candidate; verify before touching.

**Estimated total: ~71 files + docs-duplicates pass, across 4 commits, with
zero functional change — proven by the same gates every code phase used.**
