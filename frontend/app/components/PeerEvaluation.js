'use client';

import { useState, useEffect, useCallback } from 'react';
import styles from './PeerEvaluation.module.css';
// QA-2026-07-16 #2: the POST route is now facilitator-guarded, so every call
// must carry the HttpOnly JWT cookie — adminFetch is the single authed path
// (plain fetch drops the cookie in cross-origin deployments).
import { adminFetch } from '../utils/adminFetch';

export default function PeerEvaluation({ sessionId }) {
    const [evals, setEvals] = useState([]);
    const [averages, setAverages] = useState({});
    const [evaluator, setEvaluator] = useState('');
    const [target, setTarget] = useState('');
    const [contribution, setContribution] = useState(3);
    const [communication, setCommunication] = useState(3);
    const [leadership, setLeadership] = useState(3);
    const [comment, setComment] = useState('');
    const [loading, setLoading] = useState(false);

    const fetchEvals = useCallback(async () => {
        if (!sessionId) return;
        try {
            const res = await adminFetch(`/api/admin/${sessionId}/peer-evaluations`);
            if (res.ok) { const data = await res.json(); setEvals(data.evaluations || []); setAverages(data.averages || {}); }
        } catch { /* offline */ }
    }, [sessionId]);

    useEffect(() => { fetchEvals(); }, [fetchEvals]);

    const handleSubmit = async (e) => {
        e.preventDefault();
        if (!evaluator.trim() || !target.trim()) return;
        setLoading(true);
        try {
            const res = await adminFetch(`/api/admin/${sessionId}/peer-evaluations`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ evaluator_name: evaluator.trim(), target_name: target.trim(), contribution, communication, leadership, comment: comment.trim() }),
            });
            if (res.ok) { fetchEvals(); setEvaluator(''); setTarget(''); setContribution(3); setCommunication(3); setLeadership(3); setComment(''); }
        } catch { /* error */ }
        finally { setLoading(false); }
    };

    const handleDelete = async (evalId) => {
        if (!confirm('Delete this evaluation?')) return;
        try {
            const res = await adminFetch(`/api/admin/${sessionId}/peer-evaluations/${evalId}`, { method: 'DELETE' });
            if (res.ok) fetchEvals();
        } catch { /* error */ }
    };

    const StarRating = ({ value, onChange, label }) => (
        <div className={styles.ratingGroup}>
            <span className={styles.ratingLabel}>{label}</span>
            <div className={styles.stars}>
                {[1, 2, 3, 4, 5].map(n => (
                    <button key={n} type="button" className={`${styles.star} ${n <= value ? styles.starActive : ''}`} onClick={() => onChange(n)}>★</button>
                ))}
            </div>
        </div>
    );

    if (!sessionId) {
        return (<div className={styles.container}><div className={styles.header}><span className={styles.icon}>🤝</span><div><h2 className={styles.title}>Peer Evaluations</h2><p className={styles.subtitle}>Select a session from the Leaderboard.</p></div></div><div className={styles.empty}>Select a session first.</div></div>);
    }

    return (
        <div className={styles.container}>
            <div className={styles.header}><span className={styles.icon}>🤝</span><div><h2 className={styles.title}>Peer Evaluations</h2><p className={styles.subtitle}>Submit and view team contribution assessments.</p></div></div>

            <form className={styles.form} onSubmit={handleSubmit}>
                <div className={styles.formRow2}>
                    <input className={styles.input} placeholder="Evaluator name" value={evaluator} onChange={(e) => setEvaluator(e.target.value)} required />
                    <input className={styles.input} placeholder="Target name" value={target} onChange={(e) => setTarget(e.target.value)} required />
                </div>
                <div className={styles.ratingsRow}>
                    <StarRating value={contribution} onChange={setContribution} label="Contribution" />
                    <StarRating value={communication} onChange={setCommunication} label="Communication" />
                    <StarRating value={leadership} onChange={setLeadership} label="Leadership" />
                </div>
                <input className={styles.input} placeholder="Comment (optional)" value={comment} onChange={(e) => setComment(e.target.value)} />
                <button className={styles.submitBtn} type="submit" disabled={loading}>{loading ? '⏳' : '📝'} Submit Evaluation</button>
            </form>

            {/* ── Averages ── */}
            {Object.keys(averages).length > 0 && (
                <div className={styles.avgSection}>
                    <h3 className={styles.avgTitle}>Average Scores</h3>
                    <table className={styles.table}>
                        <thead><tr><th>Player</th><th>Contribution</th><th>Communication</th><th>Leadership</th><th>Reviews</th></tr></thead>
                        <tbody>
                            {Object.entries(averages).map(([name, data]) => (
                                <tr key={name}>
                                    <td className={styles.playerName}>{name}</td>
                                    <td>{data.contribution_avg} ★</td>
                                    <td>{data.communication_avg} ★</td>
                                    <td>{data.leadership_avg} ★</td>
                                    <td>{data.total_reviews}</td>
                                </tr>
                            ))}
                        </tbody>
                    </table>
                </div>
            )}

            {/* ── Individual Evaluations ── */}
            <div className={styles.evalList}>
                {evals.length === 0 ? <div className={styles.empty}>No evaluations yet.</div> : evals.map(ev => (
                    <div key={ev.eval_id} className={styles.evalCard}>
                        <div className={styles.evalHeader}>
                            <span><strong>{ev.evaluator_name}</strong> → <strong>{ev.target_name}</strong></span>
                            <span className={styles.evalTime}>{new Date(ev.created_at).toLocaleString()}</span>
                        </div>
                        <div className={styles.evalScores}>
                            <span>📊 {ev.contribution}</span>
                            <span>💬 {ev.communication}</span>
                            <span>👑 {ev.leadership}</span>
                        </div>
                        {ev.comment && <p className={styles.evalComment}>{ev.comment}</p>}
                        <button className={styles.deleteBtn} onClick={() => handleDelete(ev.eval_id)}>🗑️</button>
                    </div>
                ))}
            </div>
        </div>
    );
}
