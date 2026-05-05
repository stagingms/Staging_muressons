'use client';
import { useState, useEffect, useCallback } from 'react';

/**
 * OnboardingWizard — First-time guided tour for admin dashboards.
 * Shows a step-by-step overlay explaining key areas and features.
 * Remembers completion in localStorage to never show again.
 *
 * Props:
 *   mode: 'god_mode' | 'facilitator'
 *   onComplete: called when wizard is dismissed
 *   userId: facilitator/admin ID for localStorage key
 */

const GOD_MODE_STEPS = [
    {
        title: 'Welcome to God Mode 👑',
        icon: '🎉',
        body: 'You have full Super Administrator control over the entire Muressons simulation platform. This quick tour will show you the key areas.',
        color: '#f59e0b',
        tabHint: null,
    },
    {
        title: 'Command Center',
        icon: '📡',
        body: 'Your starting point — the System Overview shows real-time session health, pedagogical scaffolding toggles, and platform-wide KPI gauges. The Platform Analytics tab provides aggregated metrics across all cohorts.',
        color: '#3b82f6',
        tabHint: 'system_overview',
    },
    {
        title: 'Cohort Orchestration',
        icon: '🎓',
        body: 'Manage facilitators (create accounts, assign roles), provision cohorts, control round pacing, and send universal broadcasts. The 3-tier role system (Super Admin → Lead → Base) is enforced here.',
        color: '#8b5cf6',
        tabHint: 'facilitator_management',
    },
    {
        title: 'Engine Configuration',
        icon: '⚙️',
        body: 'Tune the simulation engine: adjust macro-economic baselines, configure materiality matrices, edit archetype profiles, and test the scorecard formula. Changes here affect ALL cohorts.',
        color: '#06b6d4',
        tabHint: 'engine_config',
    },
    {
        title: 'Pedagogical Scaffolding',
        icon: '🔮',
        body: 'Toggle 11 learning scaffolds: Prediction Gates, Confidence Calibration, Board Room Moments, Case Cards, Strategy Memos, and more. Hover each toggle for a detailed description of its student-facing behaviour.',
        color: '#a855f7',
        tabHint: 'pedagogical_toggles',
    },
    {
        title: 'Danger Zone',
        icon: '☢️',
        body: 'Backup & Export creates full system snapshots (JSON/CSV). Import restores from backups. GDPR exports individual player data. Factory Reset requires a typed confirmation phrase and 15-second countdown.',
        color: '#ef4444',
        tabHint: 'backup_export',
    },
    {
        title: 'Keyboard Shortcuts',
        icon: '⌨️',
        body: 'Quick navigation: Ctrl+1 through Ctrl+5 opens sidebar categories. Ctrl+B jumps to Session Controls. All scaffolding toggles show descriptions on hover.',
        color: '#22c55e',
        tabHint: null,
    },
];

const FACILITATOR_STEPS = [
    {
        title: 'Welcome, Facilitator! 🎓',
        icon: '🎉',
        body: 'This dashboard gives you everything you need to run the Muressons simulation for your cohorts. Let\'s take a quick tour of the key areas.',
        color: '#3b82f6',
        tabHint: null,
    },
    {
        title: 'Command Center',
        icon: '🎯',
        body: 'Dashboard Home shows your cohort count, player enrollment, and KPI health alerts. The Round Timeline visualises progress across cohorts. The Teleprompter provides round-by-round speaking scripts.',
        color: '#6366f1',
        tabHint: 'dashboard_home',
    },
    {
        title: 'Live Classroom',
        icon: '👥',
        body: 'During live sessions: view the Player Registry, inspect individual sessions with Session Viewer, impersonate any team to see their cockpit, send narrative messages via Swipe File, or broadcast to all teams.',
        color: '#8b5cf6',
        tabHint: 'player_registry',
    },
    {
        title: 'Analytics & Assessment',
        icon: '📊',
        body: 'Deep analytics: Decision Heatmaps, Cohort Comparisons, Complexity Feed, and Decision History. Use the Scorecard Sandbox to demonstrate the scoring formula. Export Reports generates CSV/PDF for grading.',
        color: '#06b6d4',
        tabHint: 'decision_heatmap',
    },
    {
        title: 'Configuration',
        icon: '⚙️',
        body: 'Set Auto-Pause triggers to automatically halt rounds at critical thresholds. Use Undo Round to roll back mistakes. The Teaching Journal is your private workspace for notes and annotations.',
        color: '#f59e0b',
        tabHint: 'auto_pause',
    },
    {
        title: 'Session Context',
        icon: '🔗',
        body: 'Click any cohort in the Leaderboard to set it as your active session context. This filters Session Viewer, Swipe File, and Manual Overrides to that specific cohort. Your selection persists across page reloads.',
        color: '#22c55e',
        tabHint: 'leaderboard',
    },
    {
        title: 'Notification Bell',
        icon: '🔔',
        body: 'The bell icon in the sidebar header shows real-time notifications from God Mode: settings changes, pacing overrides, and system freeze events. The badge shows unread count.',
        color: '#ef4444',
        tabHint: null,
    },
    {
        title: 'Role Permissions',
        icon: '🔐',
        body: 'Your available tabs depend on your role. Base Facilitators see core teaching tools. Lead Facilitators unlock Manual Overrides, Materiality Matrix, and Activity Logs. Super Admins have full access.',
        color: '#a855f7',
        tabHint: null,
    },
];

export default function OnboardingWizard({ mode = 'facilitator', onComplete, userId = '', onStepChange }) {
    const storageKey = `muressons_onboarding_${mode}_${userId}`;
    const [visible, setVisible] = useState(false);
    const [step, setStep] = useState(0);

    const steps = mode === 'god_mode' ? GOD_MODE_STEPS : FACILITATOR_STEPS;

    useEffect(() => {
        if (typeof window === 'undefined') return;
        const seen = localStorage.getItem(storageKey);
        if (!seen) setVisible(true);
    }, [storageKey]);

    // Navigate the parent dashboard to the relevant tab when step changes
    useEffect(() => {
        if (!visible) return;
        const current = steps[step];
        if (current?.tabHint && onStepChange) {
            onStepChange(current.tabHint);
        }
    }, [step, visible, steps, onStepChange]);

    const handleDismiss = useCallback(() => {
        localStorage.setItem(storageKey, 'true');
        setVisible(false);
        onComplete?.();
    }, [storageKey, onComplete]);

    const handleNext = useCallback(() => {
        if (step < steps.length - 1) {
            setStep(s => s + 1);
        } else {
            handleDismiss();
        }
    }, [step, steps.length, handleDismiss]);

    const handlePrev = useCallback(() => {
        setStep(s => Math.max(0, s - 1));
    }, []);

    if (!visible) return null;

    const current = steps[step];
    const progress = ((step + 1) / steps.length) * 100;

    return (
        <div style={{
            position: 'fixed', inset: 0, zIndex: 20000,
            display: 'flex', alignItems: 'center', justifyContent: 'center',
            background: 'rgba(0,0,0,0.45)',
            backdropFilter: 'blur(3px)',
            animation: 'fadeIn 0.3s ease',
        }}>
            <style dangerouslySetInnerHTML={{ __html: `
                @keyframes fadeIn { from { opacity: 0; } to { opacity: 1; } }
                @keyframes slideUp { from { transform: translateY(24px); opacity: 0; } to { transform: translateY(0); opacity: 1; } }
                @keyframes pulseGlow { 0%, 100% { box-shadow: 0 0 0 0 rgba(99,102,241,0.3); } 50% { box-shadow: 0 0 0 8px rgba(99,102,241,0); } }
            `}} />
            <div style={{
                background: 'var(--bg-card, #1e293b)',
                border: '1px solid var(--border-subtle, #334155)',
                borderRadius: '20px',
                padding: '0',
                maxWidth: '480px',
                width: '90%',
                boxShadow: '0 20px 60px rgba(0,0,0,0.4)',
                animation: 'slideUp 0.4s ease',
                overflow: 'hidden',
            }}>
                {/* Progress bar */}
                <div style={{
                    height: '4px',
                    background: 'rgba(148,163,184,0.1)',
                }}>
                    <div style={{
                        height: '100%',
                        width: `${progress}%`,
                        background: `linear-gradient(90deg, ${current.color}, ${current.color}80)`,
                        transition: 'width 0.4s ease',
                        borderRadius: '0 2px 2px 0',
                    }} />
                </div>

                <div style={{ padding: '2rem 2.5rem 1.5rem' }}>
                    {/* Icon + Step counter */}
                    <div style={{
                        display: 'flex', justifyContent: 'space-between', alignItems: 'center',
                        marginBottom: '1rem',
                    }}>
                        <div style={{
                            fontSize: '2.5rem',
                            width: '60px', height: '60px',
                            display: 'flex', alignItems: 'center', justifyContent: 'center',
                            borderRadius: '16px',
                            background: `${current.color}15`,
                            border: `1px solid ${current.color}30`,
                        }}>
                            {current.icon}
                        </div>
                        <span style={{
                            fontSize: '0.68rem', fontWeight: 700,
                            color: 'var(--text-muted, #64748b)',
                            fontFamily: 'var(--font-mono, monospace)',
                            letterSpacing: '0.05em',
                        }}>
                            {step + 1} / {steps.length}
                        </span>
                    </div>

                    {/* Title */}
                    <h2 style={{
                        fontSize: '1.25rem', fontWeight: 800,
                        color: 'var(--text-primary, #f1f5f9)',
                        margin: '0 0 0.75rem 0',
                        lineHeight: 1.3,
                    }}>
                        {current.title}
                    </h2>

                    {/* Body */}
                    <p style={{
                        fontSize: '0.88rem',
                        color: 'var(--text-secondary, #94a3b8)',
                        lineHeight: 1.7,
                        margin: 0,
                    }}>
                        {current.body}
                    </p>
                </div>

                {/* Actions */}
                <div style={{
                    padding: '1rem 2.5rem 1.5rem',
                    display: 'flex', justifyContent: 'space-between', alignItems: 'center',
                    borderTop: '1px solid var(--border-subtle, #334155)',
                }}>
                    <div style={{ display: 'flex', gap: '0.5rem' }}>
                        {step > 0 && (
                            <button
                                onClick={handlePrev}
                                style={{
                                    padding: '0.5rem 1.2rem', borderRadius: '8px',
                                    border: '1px solid var(--border-subtle, #334155)',
                                    background: 'transparent',
                                    color: 'var(--text-muted, #64748b)',
                                    fontSize: '0.82rem', fontWeight: 600,
                                    cursor: 'pointer', transition: 'all 0.15s',
                                }}
                            >
                                ← Back
                            </button>
                        )}
                        <button
                            onClick={handleDismiss}
                            style={{
                                padding: '0.5rem 1rem', borderRadius: '8px',
                                border: 'none', background: 'transparent',
                                color: 'var(--text-muted, #64748b)',
                                fontSize: '0.75rem', fontWeight: 500,
                                cursor: 'pointer', opacity: 0.7,
                            }}
                        >
                            Skip tour
                        </button>
                    </div>
                    <button
                        onClick={handleNext}
                        style={{
                            padding: '0.6rem 1.8rem', borderRadius: '8px',
                            border: 'none',
                            background: `linear-gradient(135deg, ${current.color}, ${current.color}cc)`,
                            color: '#fff',
                            fontSize: '0.88rem', fontWeight: 700,
                            cursor: 'pointer',
                            boxShadow: `0 4px 16px ${current.color}40`,
                            transition: 'all 0.15s',
                            animation: step === steps.length - 1 ? 'pulseGlow 2s infinite' : 'none',
                        }}
                    >
                        {step === steps.length - 1 ? '✅ Get Started' : 'Next →'}
                    </button>
                </div>

                {/* Dot indicators */}
                <div style={{
                    display: 'flex', justifyContent: 'center', gap: '6px',
                    paddingBottom: '1rem',
                }}>
                    {steps.map((_, i) => (
                        <button
                            key={i}
                            onClick={() => setStep(i)}
                            style={{
                                width: i === step ? '20px' : '6px',
                                height: '6px',
                                borderRadius: '3px',
                                border: 'none',
                                background: i === step ? current.color : 'rgba(148,163,184,0.2)',
                                cursor: 'pointer',
                                transition: 'all 0.3s ease',
                                padding: 0,
                            }}
                        />
                    ))}
                </div>
            </div>
        </div>
    );
}
