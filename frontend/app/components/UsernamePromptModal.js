import React, { useState } from 'react';
import Dialog from './Dialog';
import styles from './JoinCohortModal.module.css'; // Re-use the cool styling

export default function UsernamePromptModal({ userId, role, onComplete }) {
    const [username, setUsername] = useState('');
    const [submitting, setSubmitting] = useState(false);
    const [error, setError] = useState(null);

    const handleSubmit = async (e) => {
        e.preventDefault();
        
        const trimmed = username.trim();
        if (!trimmed) {
            setError('USERNAME REQUIRED — Enter a recognizable callsign.');
            return;
        }

        if (trimmed.length < 3) {
            setError('INVALID LENGTH — Must be at least 3 characters.');
            return;
        }

        setError(null);
        setSubmitting(true);

        try {
            const API = process.env.NEXT_PUBLIC_API_URL || '';
            const res = await fetch(`${API}/api/simulations/set-username`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                credentials: 'include',
                body: JSON.stringify({
                    user_id: userId,
                    role: role,
                    username: trimmed
                })
            });

            const data = await res.json();
            
            if (!res.ok) {
                throw new Error(data.detail || 'Failed to register username.');
            }

            // Success
            onComplete(data.username);
        } catch (err) {
            setError(err.message);
            setSubmitting(false);
        }
    };

    return (
        /* A11Y-3 (UX audit #18): dialog semantics + focus management.
            dismissible=false — a player MUST set a username to proceed, so
            Escape/backdrop must not dismiss it; the form is the way out. */
        <Dialog className={styles.overlay} label="Choose your username" dismissible={false} onClose={() => {}}>
            {/* Scan-line overlay */}
            <div className={styles.scanlines} />

            {/* Main card */}
            <div className={styles.card} style={{ height: 'auto', paddingBottom: '3rem' }}>
                <div className={styles.logoSection}>
                    <div className={styles.brandName}>
                        IDENTIFICATION <span className={styles.brandAccent}>REQUIRED</span>
                    </div>
                    <div className={styles.brandSubtitle}>REGISTER UNIQUE CALLSIGN</div>
                </div>

                <div className={styles.formSection}>
                    <h2 className={styles.title} style={{ color: '#00e5c3' }}>Welcome to Global Corporation</h2>
                    <p className={styles.subtitle}>
                        This is your first login. Please choose a unique username. This will be displayed on the global leaderboards and communication channels.
                    </p>

                    <form onSubmit={handleSubmit} className={styles.form} style={{ marginTop: '2rem' }}>
                        <div className={styles.field}>
                            {/* A11Y-F10 (WCAG 1.3.1, 3.3.2): same defect class as
                                JoinCohortModal — a visible label with no
                                association, so the field's only accessible name
                                was its placeholder, which disappears on the first
                                keystroke. Found while driving the real browser
                                through the sign-in flow. */}
                            <label className={styles.label} htmlFor="username-desired">DESIRED USERNAME</label>
                            <input
                                id="username-desired"
                                type="text"
                                value={username}
                                onChange={(e) => setUsername(e.target.value)}
                                placeholder="E.g., Skyhawk99"
                                disabled={submitting}
                                className={styles.input}
                                autoComplete="off"
                                spellCheck="false"
                                maxLength={24}
                            />
                        </div>

                        {error && (
                            <div className={styles.errorBox}>
                                <span className={styles.errorIcon}>⚠</span> {error}
                            </div>
                        )}

                        <button
                            type="submit"
                            disabled={submitting || !username.trim()}
                            className={styles.submitBtn}
                            style={{ background: submitting ? '#333' : '#00e5c3', color: submitting ? '#888' : '#0a0a0f' }}
                        >
                            {submitting ? '⟳ REGISTERING...' : 'CONFIRM USERNAME'}
                        </button>
                    </form>
                </div>
            </div>
        </Dialog>
    );
}
