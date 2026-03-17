import React, { useState } from 'react';
import styles from './JoinCohortModal.module.css';
import ChangePasswordModal from './ChangePasswordModal';

export default function JoinCohortModal({ sim }) {
    const [joining, setJoining] = useState(false);
    const [error, setError] = useState(null);

    const [playerId, setPlayerId] = useState('');
    const [password, setPassword] = useState('');
    const [showChangePassword, setShowChangePassword] = useState(false);

    const handleLogin = async (e) => {
        e.preventDefault();
        if (!playerId.trim()) {
            setError('Please enter your Player ID.');
            return;
        }

        setError(null);
        setJoining(true);
        try {
            await sim.playerLogin(playerId.trim(), password.trim());
            // Modal unmounts automatically when sim.sessionId is populated
        } catch (err) {
            setError(err.message);
            setJoining(false);
        }
    };

    const handleSoloSession = async () => {
        setJoining(true);
        setError(null);
        try {
            await sim.startSession('Solo Session');
        } catch (err) {
            setError(err.message || 'Failed to start solo session.');
            setJoining(false);
        }
    };

    return (
        <div className={styles.overlay}>
            <div className={styles.card}>
                {/* Header */}
                <div className={styles.header}>
                    <div className={styles.icon}>🎮</div>
                    <h1 className={styles.title}>Player Login</h1>
                    <p className={styles.subtitle}>
                        Enter your credentials to join the Muressons Simulation.
                    </p>
                </div>

                {/* Login Form */}
                <form onSubmit={handleLogin} className={styles.form}>
                    <div className={styles.field}>
                        <label className={styles.label}>Player ID</label>
                        <input
                            type="text"
                            value={playerId}
                            onChange={(e) => setPlayerId(e.target.value.toUpperCase())}
                            placeholder="e.g. MUR-001"
                            disabled={joining}
                            className={styles.input}
                            autoComplete="off"
                        />
                    </div>

                    <div className={styles.field}>
                        <label className={styles.label}>Password</label>
                        <input
                            type="password"
                            value={password}
                            onChange={(e) => setPassword(e.target.value)}
                            placeholder="Enter password"
                            disabled={joining}
                            className={styles.input}
                        />
                        <button
                            type="button"
                            onClick={() => setShowChangePassword(true)}
                            className={styles.changePasswordLink}
                        >
                            Change Password
                        </button>
                    </div>

                    {error && (
                        <div className={styles.errorBox}>
                            {error}
                        </div>
                    )}

                    <button
                        type="submit"
                        disabled={joining || !playerId.trim()}
                        className={styles.submitBtn}
                    >
                        {joining ? '⏳ Authenticating...' : '🔐 Sign In'}
                    </button>
                </form>

                {/* Solo Session */}
                <div className={styles.divider}>
                    <span>or</span>
                </div>

                <button
                    type="button"
                    onClick={handleSoloSession}
                    disabled={joining}
                    className={styles.soloBtn}
                >
                    {joining ? '⏳ Starting...' : '🚀 Start Solo Session'}
                </button>

                <ChangePasswordModal
                    isOpen={showChangePassword}
                    onClose={() => setShowChangePassword(false)}
                />
            </div>
        </div>
    );
}
