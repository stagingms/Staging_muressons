import React, { useState, useEffect } from 'react';
import Dialog from './Dialog';
import styles from './JoinCohortModal.module.css';
import ChangePasswordModal from './ChangePasswordModal';
import PasswordInput from './PasswordInput';

export default function JoinCohortModal({ sim }) {
    const [joining, setJoining] = useState(false);
    const [error, setError] = useState(null);
    const [playerId, setPlayerId] = useState('');
    const [password, setPassword] = useState('');
    const [showChangePassword, setShowChangePassword] = useState(false);
    const [forceChangePlayerId, setForceChangePlayerId] = useState('');
    const [currentTime, setCurrentTime] = useState('');

    // Auto-open change password modal when sim signals must_change_password
    useEffect(() => {
        if (sim.mustChangePassword) {
            const pid = typeof window !== 'undefined'
                ? (localStorage.getItem('muressons_playerId') || playerId)
                : playerId;
            setForceChangePlayerId(pid.toUpperCase());
            setShowChangePassword(true);
        }
    }, [sim.mustChangePassword]);

    useEffect(() => {
        const tick = () => setCurrentTime(new Date().toLocaleTimeString('en-GB', { hour: '2-digit', minute: '2-digit', second: '2-digit' }));
        tick();
        const iv = setInterval(tick, 1000);
        return () => clearInterval(iv);
    }, []);

    // Solo access is OPT-IN (default OFF): a lead facilitator / super admin
    // enables it per workshop. Read the flag from the public global-settings
    // payload (this screen is pre-authentication) and show the button ONLY
    // when it comes back explicitly true. Fail-CLOSED — start hidden, and a
    // settings hiccup keeps it hidden — because solo is now opt-in, and
    // /solo-start refuses server-side regardless. (The default flipped from
    // opt-out on 2026-08-01.)
    const [soloEnabled, setSoloEnabled] = useState(false);
    useEffect(() => {
        const API = process.env.NEXT_PUBLIC_API_URL || '';
        fetch(`${API}/api/admin/global-settings`)
            .then((r) => (r.ok ? r.json() : null))
            .then((s) => { setSoloEnabled(s?.solo_mode_enabled === true); })
            .catch(() => setSoloEnabled(false));
    }, []);

    const handleLogin = async (e) => {
        e.preventDefault();
        if (!playerId.trim()) {
            setError('IDENTIFIER REQUIRED — Enter your assigned Player ID.');
            return;
        }
        setError(null);
        setJoining(true);
        try {
            await sim.playerLogin(playerId.trim(), password.trim());
        } catch (err) {
            setError(err.message);
            setJoining(false);
        }
    };

    const handleSoloSession = async () => {
        setJoining(true);
        setError(null);
        try {
            await sim.startSoloSession('Solo Player', 'legacy_abc');
        } catch (err) {
            setError(err.message || 'Failed to start solo session.');
            setJoining(false);
        }
    };


    return (
        /* A11Y-3 (UX audit #18): the FIRST screen every participant sees had
            no dialog role, no focus management and no Escape. dismissible=false
            because there is nothing behind it to return to — signing in is the
            only exit. */
        <Dialog className={styles.overlay} label="Sign in to Muressons" dismissible={false} onClose={() => {}}>
            {/* Scan-line overlay */}
            <div className={styles.scanlines} />

            {/* Floating particles */}
            <div className={styles.particles}>
                {Array.from({ length: 6 }).map((_, i) => (
                    <div key={i} className={styles.particle} style={{ '--delay': `${i * 1.5}s`, '--x': `${15 + i * 14}%`, '--y': `${20 + (i % 3) * 25}%` }} />
                ))}
            </div>

            {/* Main card */}
            <div className={styles.card}>
                {/* Logo */}
                <div className={styles.logoSection}>
                    <div className={styles.shieldIcon}>
                        <svg width="38" height="38" viewBox="0 0 24 24" fill="none">
                            <path d="M12 2L3 7v5c0 5.55 3.84 10.74 9 12 5.16-1.26 9-6.45 9-12V7l-9-5z" fill="rgba(0,229,195,0.15)" stroke="#00e5c3" strokeWidth="1.5"/>
                            <text x="12" y="16" textAnchor="middle" fill="#00e5c3" fontSize="10" fontWeight="900" fontFamily="DM Sans, sans-serif">M</text>
                        </svg>
                    </div>
                    <div className={styles.brandName} style={{ color: '#f5b942' }}>
                        MURESSONS GLOBAL
                    </div>
                    <div className={styles.brandSubtitle}>MURESSONS GLOBAL CORPORATION</div>
                </div>

                {/* Form Section */}
                <div className={styles.formSection}>
                    <h2 className={styles.title} style={{ color: '#00e5c3' }}>Command Access</h2>
                    <p className={styles.subtitle}>Enter credentials for secure terminal link.</p>

                    <form onSubmit={handleLogin} className={styles.form}>
                        <div className={styles.field}>
                            {/* A11Y-F1 (WCAG 1.3.1, 3.3.2): the label was visually
                                present but not ASSOCIATED — no htmlFor, no id, no
                                wrapping. axe passed it only because the placeholder
                                supplied an accessible name, which disappears the
                                moment the user types. First screen every
                                participant sees. */}
                            <label className={styles.label} htmlFor="join-player-id">EXECUTIVE IDENTIFIER</label>
                            <input
                                id="join-player-id"
                                type="text"
                                value={playerId}
                                onChange={(e) => setPlayerId(e.target.value.toUpperCase())}
                                placeholder="MUR-001"
                                disabled={joining}
                                className={styles.input}
                                autoComplete="off"
                                spellCheck="false"
                                /* Password managers tag credential fields before
                                   hydration — see PasswordInput for the rationale.
                                   Players hit this screen on their own machines,
                                   where extensions are most varied. */
                                suppressHydrationWarning
                            />
                        </div>

                        <div className={styles.field}>
                            <label className={styles.label} htmlFor="join-password">CLEARANCE CIPHER</label>
                            <PasswordInput
                                id="join-password"
                                value={password}
                                onChange={(e) => setPassword(e.target.value)}
                                placeholder="••••••••"
                                disabled={joining}
                                className={styles.input}
                            />
                        </div>

                        <div className={styles.optionsRow}>
                            {/* TF-3 (UX audit §7.7): the "REMEMBER STATION"
                                checkbox was an unbound input — no state, no
                                handler, no effect. Dead UI on the first screen
                                a participant ever sees; removed. In its place,
                                the one fact worth stating here: */}
                            <span style={{ fontSize: '0.68rem', color: '#94a3b8', letterSpacing: '0.03em' }}>
                                Driver enters the team ID. Observers use the team&apos;s -VIEW code.
                            </span>
                            <button
                                type="button"
                                onClick={() => setShowChangePassword(true)}
                                className={styles.lostCipher}
                            >
                                LOST CIPHER?
                            </button>
                        </div>

                        {error && (
                            <div className={styles.errorBox}>
                                <span className={styles.errorIcon}>⚠</span> {error}
                            </div>
                        )}

                        {/* suppressHydrationWarning: password managers stamp
                            attributes on credential-form submit buttons before
                            React hydrates (see AdminLogin). */}
                        <button
                            type="submit"
                            suppressHydrationWarning
                            disabled={joining || !playerId.trim()}
                            className={styles.submitBtn}
                        >
                            {joining ? '⟳ AUTHENTICATING...' : 'ESTABLISH LINK'}
                        </button>
                    </form>

                    {soloEnabled && (
                        <button
                            type="button"
                            onClick={handleSoloSession}
                            disabled={joining}
                            className={styles.soloBtn}
                        >
                            {joining ? '⟳ INITIALIZING...' : 'START SOLO SESSION'}
                        </button>
                    )}

                    <p style={{
                        marginTop: '1rem', fontSize: '0.68rem', color: '#475569',
                        textAlign: 'center', lineHeight: 1.5, letterSpacing: '0.02em'
                    }}>
                        Your Executive Identifier (e.g. MUR-001) and your temporary <strong style={{ color: '#00e5c3' }}>Clearance Cipher</strong> are both provided by your facilitator — you will be prompted to set a personal password on your first login.
                    </p>
                </div>

                {/* Footer status */}
                <div className={styles.footerStatus}>
                    <span className={styles.statusDot} data-status="green" />
                    <span>ENCRYPTED</span>
                    <span className={styles.statusSep}>•</span>
                    <span className={styles.statusDot} data-status="amber" />
                    <span>V4.12.0</span>
                </div>
            </div>

            {/* Bottom bar */}
            <div className={styles.bottomBar}>
                <span className={styles.bottomHash}>
                    {Array.from({ length: 5 }).map((_, i) => (
                        <span key={i}>{Math.random().toString(36).slice(2, 7).toUpperCase()} </span>
                    ))}
                </span>
                <span className={styles.bottomRight}>
                    <span className={styles.bottomLabel}>LOCAL OPS</span>
                    <span className={styles.bottomTime}>{currentTime}</span>
                    <span className={styles.themeIcon}>☾</span>
                </span>
            </div>

            <ChangePasswordModal
                isOpen={showChangePassword}
                onClose={() => {
                    // Only allow closing if not a forced change
                    if (!sim.mustChangePassword) {
                        setShowChangePassword(false);
                    }
                }}
                prefillPlayerId={forceChangePlayerId || ''}
                isForced={sim.mustChangePassword}
                onSuccess={() => {
                    setShowChangePassword(false);
                    if (sim.setMustChangePassword) sim.setMustChangePassword(false);
                }}
            />
        </Dialog>
    );
}
