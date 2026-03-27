import Link from 'next/link';
import styles from './gateway.module.css';

export const metadata = {
    title: 'Admin Gateway | Muressons System',
};

export default function AdminGateway() {
    return (
        <div className={styles.gatewayContainer}>
            <header className={styles.header}>
                <div className={styles.brand}>Global Command</div>
                <h1 className={styles.title}>System Access Portal</h1>
            </header>

            <main className={styles.cardsGrid}>


                {/* ── Facilitator Card ── */}
                <Link href="/admin/facilitator" className={`${styles.roleCard} ${styles.facilitator}`}>
                    <div className={styles.icon}>🎓</div>
                    <h2 className={styles.roleTitle}>Workshop Facilitator</h2>
                    <p className={styles.roleDesc}>
                        Live session command center. Monitor active leaderboards, perform Team overrides, inject Swipe File documents, and manage active session lifecycles.
                    </p>
                    <div className={styles.enterBtn}>
                        Enter Live Control Room
                        <span className={styles.arrow}>→</span>
                    </div>
                </Link>
            </main>
        </div>
    );
}
