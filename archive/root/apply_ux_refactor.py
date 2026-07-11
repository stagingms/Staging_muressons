import re

with open('frontend/app/admin/god-mode/page.js', 'r', encoding='utf-8') as f:
    content = f.read()

# 1. Add SystemContextBar Component
context_bar = """
/* ═════════════════════════════════════════════════════════════════
 *  SYSTEM CONTEXT BAR
 * ═════════════════════════════════════════════════════════════════ */
function SystemContextBar() {
    const [status, setStatus] = useState(null);

    useEffect(() => {
        const fetchStatus = () => {
            fetch(`${API}/api/admin/system-status`)
                .then(r => r.json())
                .then(d => setStatus(d))
                .catch(() => {});
        };
        fetchStatus();
        const t = setInterval(fetchStatus, 15000);
        return () => clearInterval(t);
    }, []);

    const activeCohorts = status ? status.active_cohorts : 0;
    const activePlayers = status ? status.total_players : 0;
    const isOptimal = status ? status.system_memory_mb < 500 : true;

    return (
        <div style={{
            display: 'flex', alignItems: 'center', justifyContent: 'space-between',
            background: 'var(--bg-elevated)', borderBottom: '1px solid var(--border-subtle)',
            padding: '8px 24px', fontSize: '0.75rem', fontWeight: 600, color: 'var(--text-muted)',
            position: 'sticky', top: 0, zIndex: 10
        }}>
            <div style={{ display: 'flex', gap: '1.5rem' }}>
                <span style={{ color: '#38bdf8' }}>📡 COMMAND UPLINK</span>
                <span>Live Cohorts: <span style={{ color: 'var(--text-primary)' }}>{activeCohorts}</span></span>
                <span>Active Players: <span style={{ color: 'var(--text-primary)' }}>{activePlayers}</span></span>
            </div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                System Health: {isOptimal ? <span style={{ color: '#10b981' }}>🟢 Optimal</span> : <span style={{ color: '#ef4444' }}>🔴 Warning</span>}
            </div>
        </div>
    );
}

"""

# Insert SystemContextBar before GodModeDashboard
content = content.replace('function GodModeDashboard({ authData, onLogout }) {', context_bar + 'function GodModeDashboard({ authData, onLogout }) {')


# 2. Update SIDEBAR_CONFIG
new_sidebar = """    const SIDEBAR_CONFIG = [
        {
            category: 'Command Center',
            icon: '📡',
            id: 'command_center',
            items: [
                { id: 'system_overview',     label: 'System Overview',       icon: '📊', tooltip: 'Unified dashboard of system status and session health' },
                { id: 'platform_analytics',  label: 'Platform Analytics',  icon: '📈', tooltip: 'Aggregated macro statistics across all active cohorts' },
                { id: 'activity_log',         label: 'Activity & Complexity', icon: '📋', tooltip: 'Immutable record and live firehose of systemic interactions' },
            ]
        },
        {
            category: 'Cohort Orchestration',
            icon: '🎓',
            id: 'orchestration',
            items: [
                { id: 'cohort_orchestration', label: 'Cohort Manager',  icon: '🗂️', tooltip: 'Provision cohorts and manage facilitator access' },
                { id: 'session_controls',    label: 'Session Controls',      icon: '🎛️', tooltip: 'Round pacing, broadcasts, and visibility controls' },
                { id: 'master_interventions', label: 'Team Interventions', icon: '🚀', tooltip: 'Directly inject capital or penalties into target teams' },
                { id: 'crisis_overrides',      label: 'Crisis Overrides',    icon: '🚨', tooltip: 'Manually activate crises or deploy Black Swans' },
            ]
        },
        {
            category: 'Engine Configuration',
            icon: '⚙️',
            id: 'engine_core',
            items: [
                { id: 'macro_economics',    label: 'Macro Economics',      icon: '🔧', tooltip: 'Adjust global economic baselines and override master variables' },
                { id: 'model_parameters',  label: 'Model Parameters',    icon: '🦭', tooltip: 'Configure decision modes, materiality, and archetypes' },
                { id: 'scorecard_evaluator',label: 'Scorecard Evaluator',  icon: '📊', tooltip: 'Audit calculation logic for the Balanced Scorecard' },
            ]
        },
        {
            category: 'Resources & Content',
            icon: '📚',
            id: 'content',
            items: [
                { id: 'resources',          label: 'Resource Library',    icon: '📁', tooltip: 'Manage unlockable swipe files and PDFs for teams' },
                { id: 'glossary_editor',    label: 'Glossary Editor',     icon: '📖', tooltip: 'Edit the in-game definitions and term glossary' },
                { id: 'doc_reference',      label: 'Documentation', icon: '📑', tooltip: 'Developer documentation and live simulation reference' },
            ]
        },
        {
            category: 'Danger Zone',
            icon: '☢️',
            id: 'danger',
            items: [
                { id: 'system_export',  label: 'Backup & Export', icon: '💾', tooltip: 'Download comprehensive simulation snapshots as CSV' },
                { id: 'session_reset', label: 'Factory Reset', icon: '💥', tooltip: 'Hard wipe databases and permanently destroy cohort data' },
            ]
        }
    ];"""

content = re.sub(r'const SIDEBAR_CONFIG = \[.*?\];', new_sidebar, content, flags=re.DOTALL)


# 3. Update Initial State
new_state = """    const [activeTab, setActiveTab] = useState('system_overview');
    const [showChangePw, setShowChangePw] = useState(false);
    const [openCategories, setOpenCategories] = useState({
        command_center: true,
        orchestration: true,
        engine_core: false,
        content: false,
        danger: false,
    });"""

content = re.sub(r'const \[activeTab, setActiveTab\] = useState\([^;]+;\s*const \[showChangePw, setShowChangePw\] = useState\([^;]+;\s*const \[openCategories, setOpenCategories\] = useState\(\{[^\}]+\}\);', new_state, content, flags=re.DOTALL)


# 4. Update getTabMeta fallback
content = content.replace("return { label: 'Overview', category: 'System & Monitoring', categoryIcon: '🎯' };", "return { label: 'Overview', category: 'Command Center', categoryIcon: '📡' };")


# 5. Inject Sticky Header in layout
main_panel_start = '<main className={styles.mainPanel}>'
if main_panel_start in content:
    content = content.replace(main_panel_start, f'{main_panel_start}\n                <SystemContextBar />')


# 6. Update renderActiveComponent cases
# We'll completely replace the switch block inside renderActiveComponent
new_render = """    const renderActiveComponent = () => {
        switch (activeTab) {
            case 'system_overview':
                return (
                    <div style={{ display: 'flex', flexDirection: 'column', gap: '2rem' }}>
                        <GodModeStatus />
                        <SessionHealthDashboard />
                    </div>
                );
            case 'activity_log':
                return (
                    <div style={{ display: 'flex', flexDirection: 'column', gap: '2rem' }}>
                        <GodModeAuditLog />
                        <ComplexityEventFeed sessionId={null} />
                    </div>
                );
            case 'platform_analytics':
                return <PlatformAnalytics />;
                
            case 'cohort_orchestration':
                return (
                    <div style={{ display: 'flex', flexDirection: 'column', gap: '2rem' }}>
                        <SimulationManager fetchInternal={true} leaderboard={[]} />
                        <FacilitatorManager onNavigate={(tab) => setActiveTab(tab)} />
                    </div>
                );
            case 'session_controls':
                return (
                    <div style={{ display: 'flex', flexDirection: 'column', gap: '2rem' }}>
                        <RoundPacingControl />
                        <UniversalBroadcast />
                        <AnalyticsControlPanel />
                    </div>
                );
            case 'master_interventions':
                return <MasterInterventions />;
            case 'crisis_overrides':
                return (
                    <div style={{ display: 'flex', flexDirection: 'column', gap: '2rem' }}>
                        <CrisisTriggerConfig />
                        <CustomBlackSwanBuilder />
                    </div>
                );
                
            case 'macro_economics':
                return (
                    <div style={{ display: 'flex', flexDirection: 'column', gap: '2rem' }}>
                        <EconomicEngineTunables />
                        <MasterVariableEditor />
                    </div>
                );
            case 'model_parameters':
                return (
                    <div style={{ display: 'flex', flexDirection: 'column', gap: '2rem' }}>
                        <DecisionParadigmConfig sessions={[]} apiBase={API} />
                        <MaterialityConfig />
                        <ArchetypeEditor />
                    </div>
                );
            case 'scorecard_evaluator':
                return <div style={{padding:'1.5rem'}}><BalancedScorecardEvaluator /></div>;
                
            case 'resources':
                return <ResourceManager />;
            case 'glossary_editor':
                return <GlossaryManager />;
            case 'doc_reference':
                return (
                    <div style={{ display: 'flex', flexDirection: 'column', gap: '2rem' }}>
                        <div style={{ padding: '1.5rem', background: 'var(--bg-card)', borderRadius: '12px' }}><TechnicalGlossary /></div>
                        <SimulationReference />
                    </div>
                );
                
            case 'system_export':
                return <SystemExport />;
            case 'session_reset':
                return <DangerZonePanel apiBase={API} />;
                
            default:
                return (
                    <div className={styles.placeholder}>
                        <h2>Select a tool from the sidebar</h2>
                    </div>
                );
        }
    };"""

content = re.sub(r'const renderActiveComponent = \(\) => \{.*?^\s*};\n' , new_render + '\n', content, flags=re.DOTALL | re.MULTILINE)

with open('frontend/app/admin/god-mode/page.js', 'w', encoding='utf-8') as f:
    f.write(content)

print("Successfully refactored god-mode/page.js")
