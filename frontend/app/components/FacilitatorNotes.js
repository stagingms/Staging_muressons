'use client';

import { useState, useEffect, useCallback } from 'react';
import styles from './FacilitatorNotes.module.css';

const API = process.env.NEXT_PUBLIC_API_URL || '';

export default function FacilitatorNotes({ sessionId }) {
    const [notes, setNotes] = useState([]);
    const [text, setText] = useState('');
    const [roundNum, setRoundNum] = useState('');
    const [visible, setVisible] = useState(false);
    const [loading, setLoading] = useState(false);

    const fetchNotes = useCallback(async () => {
        if (!sessionId) return;
        try {
            const res = await fetch(`${API}/api/admin/${sessionId}/notes`);
            if (res.ok) { const data = await res.json(); setNotes(data.notes || []); }
        } catch { /* offline */ }
    }, [sessionId]);

    useEffect(() => { fetchNotes(); }, [fetchNotes]);

    const handleSubmit = async (e) => {
        e.preventDefault();
        if (!text.trim() || !sessionId) return;
        setLoading(true);
        try {
            const res = await fetch(`${API}/api/admin/${sessionId}/notes`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    text: text.trim(),
                    round_number: roundNum ? parseInt(roundNum) : null,
                    visible_to_players: visible,
                }),
            });
            if (res.ok) { const note = await res.json(); setNotes(prev => [note, ...prev]); setText(''); setRoundNum(''); setVisible(false); }
        } catch { /* error */ }
        finally { setLoading(false); }
    };

    const handleDelete = async (noteId) => {
        if (!confirm('Delete this note?')) return;
        try {
            const res = await fetch(`${API}/api/admin/${sessionId}/notes/${noteId}`, { method: 'DELETE' });
            if (res.ok) setNotes(prev => prev.filter(n => n.note_id !== noteId));
        } catch { /* error */ }
    };

    if (!sessionId) {
        return (
            <div className={styles.container}>
                <div className={styles.header}><span className={styles.icon}>📝</span><div><h2 className={styles.title}>Facilitator Notes</h2><p className={styles.subtitle}>Select a session from the Leaderboard to add notes.</p></div></div>
                <div className={styles.empty}>Select a session first.</div>
            </div>
        );
    }

    return (
        <div className={styles.container}>
            <div className={styles.header}>
                <span className={styles.icon}>📝</span>
                <div>
                    <h2 className={styles.title}>Facilitator Notes</h2>
                    <p className={styles.subtitle}>Add comments and annotations for this session. Optionally make them visible to players.</p>
                </div>
            </div>

            <form className={styles.form} onSubmit={handleSubmit}>
                <textarea className={styles.textarea} placeholder="Type your note here..." value={text} onChange={(e) => setText(e.target.value)} rows={3} disabled={loading} />
                <div className={styles.formRow}>
                    <input className={styles.roundInput} type="number" min="1" max="10" placeholder="Round #" value={roundNum} onChange={(e) => setRoundNum(e.target.value)} />
                    <label className={styles.visibleToggle}>
                        <input type="checkbox" checked={visible} onChange={(e) => setVisible(e.target.checked)} />
                        <span>Visible to players</span>
                    </label>
                    <button className={styles.submitBtn} type="submit" disabled={loading || !text.trim()}>
                        {loading ? '⏳' : '💬'} Add Note
                    </button>
                </div>
            </form>

            <div className={styles.notesList}>
                {notes.length === 0 ? (
                    <div className={styles.empty}>No notes yet. Add one above.</div>
                ) : (
                    notes.map(note => (
                        <div key={note.note_id} className={styles.noteCard}>
                            <div className={styles.noteMeta}>
                                <span className={styles.noteTime}>{new Date(note.created_at).toLocaleString()}</span>
                                {note.round_number && <span className={styles.noteRound}>R{note.round_number}</span>}
                                {note.visible_to_players && <span className={styles.noteVisible}>👁️ Visible</span>}
                            </div>
                            <p className={styles.noteText}>{note.text}</p>
                            <button className={styles.deleteBtn} onClick={() => handleDelete(note.note_id)}>🗑️</button>
                        </div>
                    ))
                )}
            </div>
        </div>
    );
}
