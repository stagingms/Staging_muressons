'use client';

import { useState, useEffect, useCallback } from 'react';
import styles from './ThemeToggle.module.css';

/**
 * ThemeToggle — Animated dark/light mode switcher.
 * Persists selection to localStorage and syncs `data-theme` on <html>.
 */
export default function ThemeToggle() {
    const [theme, setTheme] = useState(() => {
        if (typeof window === 'undefined') return 'dark';
        return localStorage.getItem('muressons-theme') ||
            (window.matchMedia('(prefers-color-scheme: light)').matches ? 'light' : 'dark');
    });
    const [mounted, setMounted] = useState(false);

    // Sync DOM attribute and mark as mounted on first client render
    useEffect(() => {
        document.documentElement.setAttribute('data-theme', theme);
        setMounted(true);
    // eslint-disable-next-line react-hooks/exhaustive-deps
    }, []);


    const toggle = useCallback(() => {
        setTheme((prev) => {
            const next = prev === 'dark' ? 'light' : 'dark';
            document.documentElement.setAttribute('data-theme', next);
            localStorage.setItem('muressons-theme', next);
            return next;
        });
    }, []);

    // Prevent flash of wrong icon during SSR
    if (!mounted) return null;

    const isDark = theme === 'dark';

    return (
        <button
            className={styles.toggle}
            onClick={toggle}
            aria-label={`Switch to ${isDark ? 'light' : 'dark'} mode`}
            title={`Switch to ${isDark ? 'light' : 'dark'} mode`}
        >
            <div className={`${styles.iconWrapper} ${isDark ? styles.dark : styles.light}`}>
                {/* Sun */}
                <svg
                    className={`${styles.icon} ${styles.sun} ${isDark ? '' : styles.active}`}
                    viewBox="0 0 24 24"
                    fill="none"
                    stroke="currentColor"
                    strokeWidth="2"
                    strokeLinecap="round"
                    strokeLinejoin="round"
                >
                    <circle cx="12" cy="12" r="5" />
                    <line x1="12" y1="1" x2="12" y2="3" />
                    <line x1="12" y1="21" x2="12" y2="23" />
                    <line x1="4.22" y1="4.22" x2="5.64" y2="5.64" />
                    <line x1="18.36" y1="18.36" x2="19.78" y2="19.78" />
                    <line x1="1" y1="12" x2="3" y2="12" />
                    <line x1="21" y1="12" x2="23" y2="12" />
                    <line x1="4.22" y1="19.78" x2="5.64" y2="18.36" />
                    <line x1="18.36" y1="5.64" x2="19.78" y2="4.22" />
                </svg>

                {/* Moon */}
                <svg
                    className={`${styles.icon} ${styles.moon} ${isDark ? styles.active : ''}`}
                    viewBox="0 0 24 24"
                    fill="none"
                    stroke="currentColor"
                    strokeWidth="2"
                    strokeLinecap="round"
                    strokeLinejoin="round"
                >
                    <path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z" />
                </svg>
            </div>
        </button>
    );
}
