import React from 'react';
import styles from './DecisionModal.module.css';
import Dialog from './Dialog';

export default function CFOOverrideModal({ onConfirm, onCancel, errorText }) {
    return (
        /* A11Y-3 (UX audit #18): dialog semantics, Escape, focus trap +
            restore via the shared Dialog primitive. Markup/styling unchanged. */
        <Dialog className={styles.modalOverlay} onClose={onCancel} labelledBy="cfo-override-title">
            <div className={styles.modalContent} style={{ maxWidth: '500px' }}>
                <h2 id="cfo-override-title" style={{ color: '#ff4d4f', borderBottom: '1px solid #333', paddingBottom: '10px' }}>⚠️ CFO Validation Override</h2>

                <p style={{ marginTop: '20px', fontSize: '0.95rem', color: '#ccc', lineHeight: '1.5' }}>
                    The finance department has flagged your budget allocation:
                </p>

                <div style={{ background: '#222', padding: '15px', borderRadius: '4px', marginTop: '10px', marginBottom: '20px', borderLeft: '4px solid #ff4d4f' }}>
                    <code>{errorText || "Proposed initiative lacks material justification."}</code>
                </div>

                <p style={{ fontSize: '0.9rem', color: '#999', marginBottom: '25px' }}>
                    You may force this executive decision through, but doing so goes against established Double Materiality guidelines. This will significantly impact your Corporate Treasury and Governance Reputation.
                </p>

                <div className={styles.buttonGroup}>
                    <button
                        className={styles.cancelBtn}
                        onClick={onCancel}
                        style={{ flex: 1, padding: '12px', background: '#333', color: '#fff' }}
                    >
                        Review Allocations
                    </button>

                    <button
                        className={styles.submitBtn}
                        onClick={onConfirm}
                        style={{ flex: 1, padding: '12px', background: '#ff4d4f', color: '#fff', border: 'none', borderRadius: '4px', cursor: 'pointer' }}
                    >
                        Force Bypass (Penalty)
                    </button>
                </div>
            </div>
        </Dialog>
    );
}
