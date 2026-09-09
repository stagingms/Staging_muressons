/**
 * The [object Object] ban.
 *
 * THE DEFECT
 *   `throw new Error(data.detail || fallback)` assumes FastAPI's `detail` is a
 *   string. It is a string only for a plain HTTPException: a 422 returns an
 *   ARRAY of {loc, msg, type} and a structured raise returns a dict, and
 *   `new Error()` coerces either to the literal text "[object Object]". The
 *   cohort setup form showed exactly that instead of naming the field it had
 *   rejected — the one failure state an operator cannot act on.
 *
 * WHY A BAN AND NOT A SWEEP
 *   There were 57 of these across app/ when this was written. Fixing them one
 *   at a time is a fix that regresses the moment someone writes the 58th, and
 *   nothing in review reliably catches it because the code reads fine. So the
 *   count is frozen per file: existing sites are recorded and may only ever go
 *   DOWN, and a file not listed here may not introduce one at all.
 *
 *   Use toErrorText / describeHttpFailure from app/lib/apiError.js instead. When
 *   you convert a file, lower its number here — or delete the line when it hits
 *   zero. The test fails on an entry that is too HIGH and on one that has become
 *   stale, so the list cannot rot in either direction.
 *
 *   This mirrors backend/tests/test_no_stringified_flag_reads.py, which bans the
 *   equivalent defect shape on the server for the same reason.
 */
import fs from 'fs';
import path from 'path';

const APP = path.join(__dirname, '..', 'app');
const PATTERN = /\.detail\s*\|\|/g;

// file → number of raw `.detail ||` coercions still present. Lower is better;
// higher fails. CreateCohortModal.js is deliberately absent: it was converted.
const BASELINE = {
    'app/admin/facilitator/page.js': 3,
    'app/admin/god-mode/page.js': 3,
    'app/components/AdminLogin.js': 1,
    'app/components/AnalyticsControlPanel.js': 1,
    'app/components/ArchetypeEditor.js': 2,
    'app/components/AutoPauseConfig.js': 1,
    'app/components/BulkMessaging.js': 1,
    'app/components/ChangePasswordModal.js': 1,
    'app/components/ConfigLiveStatus.js': 1,
    'app/components/CustomBlackSwanBuilder.js': 1,
    'app/components/DebriefNarrative.js': 1,
    'app/components/DryRunSimulator.js': 1,
    'app/components/FacilitatorManager.js': 6,
    'app/components/MaterialityConfig.js': 5,
    'app/components/NegotiationRoom.js': 2,
    'app/components/PillarConfigurator.js': 2,
    'app/components/RegulatorySandboxControl.js': 2,
    'app/components/ResourceManager.js': 2,
    'app/components/RoundPacingControl.js': 2,
    'app/components/SimulationSwitchboard.js': 1,
    'app/components/StakeholderConfig.js': 7,
    'app/components/StudentBonuses.js': 1,
    'app/components/SustainabilityBalancedScorecard.js': 1,
    'app/components/SwipeFile.js': 2,
    'app/components/SystemExport.js': 1,
    'app/components/TurnaroundConsole.js': 1,
    'app/components/UndoRound.js': 1,
    'app/components/UsernamePromptModal.js': 1,
    'app/hooks/useSimulation.js': 2,
    'app/lib/apiError.js': 1,
};

const walk = (dir) => fs.readdirSync(dir, { withFileTypes: true }).flatMap((e) => {
    const full = path.join(dir, e.name);
    if (e.isDirectory()) return walk(full);
    return /\.jsx?$/.test(e.name) ? [full] : [];
});

const currentCounts = () => {
    const out = {};
    for (const file of walk(APP)) {
        const hits = (fs.readFileSync(file, 'utf8').match(PATTERN) || []).length;
        if (hits) out[path.relative(path.join(__dirname, '..'), file).replace(/\\/g, '/')] = hits;
    }
    return out;
};

describe('raw FastAPI detail coercion', () => {
    it('is not introduced in any new file', () => {
        const current = currentCounts();
        const newFiles = Object.keys(current).filter((f) => !(f in BASELINE));
        expect(newFiles).toEqual([]);
    });

    it('does not grow in any file that still has it', () => {
        const current = currentCounts();
        const grown = Object.entries(current)
            .filter(([f, n]) => f in BASELINE && n > BASELINE[f])
            .map(([f, n]) => `${f}: ${n} (baseline ${BASELINE[f]})`);
        expect(grown).toEqual([]);
    });

    it('has no stale baseline entries', () => {
        const current = currentCounts();
        const stale = Object.entries(BASELINE)
            .filter(([f, n]) => (current[f] || 0) < n)
            .map(([f, n]) => `${f}: now ${current[f] || 0}, baseline says ${n} — lower it`);
        expect(stale).toEqual([]);
    });

    it('keeps the converted cohort form clean', () => {
        const current = currentCounts();
        expect(current['app/components/CreateCohortModal.js']).toBeUndefined();
    });
});
