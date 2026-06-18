'use client';
import { useState, useEffect } from 'react';
import styles from './IndustryBenchmarkPanel.module.css';

const API = process.env.NEXT_PUBLIC_API_URL || '';

/* ─── Helpers ─── */
function getPercentileInfo(percentile) {
    if (percentile >= 75) return { label: '🏆 Top Quartile', color: '#10b981', bg: 'rgba(16,185,129,0.12)' };
    if (percentile >= 50) return { label: '🔵 Above Median', color: '#3b82f6', bg: 'rgba(59,130,246,0.12)' };
    if (percentile >= 25) return { label: '🟡 Below Median', color: '#f59e0b', bg: 'rgba(245,158,11,0.12)' };
    return { label: '🔴 Bottom Quartile', color: '#ef4444', bg: 'rgba(239,68,68,0.12)' };
}

function PercentileBar({ playerValue, p25, p75, unit }) {
    const range = p75 - p25;
    if (!range || range <= 0) {
        return <div className={styles.barPlaceholder}>P25–P75 range unavailable</div>;
    }

    // Clamp the player position within the bar
    const rawPct = ((playerValue - p25) / range) * 100;
    const pct = Math.min(100, Math.max(0, rawPct));

    return (
        <div className={styles.barContainer}>
            <div className={styles.barTrack}>
                <div className={styles.barFill} style={{ width: `${pct}%` }} />
                <div
                    className={styles.barThumb}
                    style={{ left: `${pct}%` }}
                    title={`${playerValue}${unit ? ` ${unit}` : ''}`}
                />
            </div>
            <div className={styles.barLabels}>
                <span>P25: {p25}{unit ? ` ${unit}` : ''}</span>
                <span>P75: {p75}{unit ? ` ${unit}` : ''}</span>
            </div>
        </div>
    );
}

function MetricCard({ metric }) {
    const { label, unit, player_value, p25, p75, percentile, description, icon } = metric;
    const pInfo = getPercentileInfo(percentile);

    return (
        <div className={styles.metricCard}>
            <div className={styles.metricHeader}>
                <span className={styles.metricIcon}>{icon || '📊'}</span>
                <div>
                    <div className={styles.metricLabel}>{label}</div>
                    {unit && <div className={styles.metricUnit}>{unit}</div>}
                </div>
            </div>

            <div className={styles.metricValueRow}>
                <span className={styles.metricValue}>
                    {typeof player_value === 'number' ? player_value.toLocaleString() : player_value}
                    {unit && <span className={styles.metricValueUnit}> {unit}</span>}
                </span>
                <span
                    className={styles.percentileBadge}
                    style={{ color: pInfo.color, background: pInfo.bg, borderColor: pInfo.color }}
                >
                    {pInfo.label}
                </span>
            </div>

            <PercentileBar playerValue={player_value} p25={p25} p75={p75} unit={unit} />

            {description && <p className={styles.metricDesc}>{description}</p>}
        </div>
    );
}

export default function IndustryBenchmarkPanel({ sessionId, buId }) {
    const [data, setData] = useState(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState('');

    useEffect(() => {
        if (!sessionId) { setLoading(false); return; }
        setLoading(true);
        setError('');

        const url = buId
            ? `${API}/api/admin/${sessionId}/industry-benchmark?bu_id=${buId}`
            : `${API}/api/admin/${sessionId}/industry-benchmark`;

        fetch(url)
            .then(r => {
                if (!r.ok) throw new Error(`HTTP ${r.status}`);
                return r.json();
            })
            .then(d => {
                setData(d);
                setLoading(false);
            })
            .catch(err => {
                setError(`Failed to load benchmark data: ${err.message}`);
                setLoading(false);
            });
    }, [sessionId, buId]);

    /* ─── Loading / error / no-session states ─── */
    if (!sessionId) {
        return (
            <div className={styles.container}>
                <div className={styles.placeholder}>
                    <div style={{ fontSize: '2.5rem', marginBottom: '0.5rem' }}>📈</div>
                    <p>Select a session to view industry benchmark comparisons.</p>
                </div>
            </div>
        );
    }

    if (loading) {
        return (
            <div className={styles.container}>
                <div className={styles.loadingState}>
                    <div className={styles.spinner} />
                    <span>Loading benchmark data…</span>
                </div>
            </div>
        );
    }

    if (error) {
        return (
            <div className={styles.container}>
                <div className={styles.errorState}>{error}</div>
            </div>
        );
    }

    if (!data) {
        return (
            <div className={styles.container}>
                <div className={styles.placeholder}>
                    <p>No benchmark data available for this session.</p>
                </div>
            </div>
        );
    }

    const metrics = data.metrics || [];
    const aboveMedian = metrics.filter(m => (m.percentile ?? 0) >= 50).length;
    const total = metrics.length || 1;
    const overallLabel = aboveMedian > total / 2 ? 'above' : aboveMedian === Math.floor(total / 2) ? 'at' : 'below';

    return (
        <div className={styles.container}>
            {/* Header */}
            <div className={styles.header}>
                <div>
                    <h3 className={styles.title}>
                        {data.vertical_icon || '📈'} {data.vertical_label || 'Industry'} — Industry Benchmark Comparison
                    </h3>
                    {data.benchmark_year && (
                        <span className={styles.yearBadge}>Benchmark Year: {data.benchmark_year}</span>
                    )}
                </div>
            </div>

            {/* Metrics grid */}
            <div className={styles.metricsGrid}>
                {metrics.map((m, idx) => (
                    <MetricCard key={m.key || idx} metric={m} />
                ))}
            </div>

            {/* Summary box */}
            <div className={styles.summaryBox}>
                <span className={styles.summaryIcon}>
                    {overallLabel === 'above' ? '🏆' : overallLabel === 'at' ? '🔵' : '⚠️'}
                </span>
                <p className={styles.summaryText}>
                    You are performing{' '}
                    <strong style={{ color: overallLabel === 'above' ? '#10b981' : overallLabel === 'at' ? '#3b82f6' : '#f59e0b' }}>
                        {overallLabel} the industry median
                    </strong>{' '}
                    across <strong>{aboveMedian} of {total}</strong> key metric{total !== 1 ? 's' : ''}.
                </p>
            </div>
        </div>
    );
}
