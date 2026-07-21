'use client';
import { useState } from 'react';

/**
 * PasswordInput — drop-in replacement for <input type="password"> with an
 * optional visibility toggle (👁 / 🙈). All props pass straight through to
 * the underlying input; the toggle is type="button" so it can never submit
 * a form, and it flips only the input's type attribute — nothing about the
 * auth flow changes. Used on every login and password-entry surface.
 */
export default function PasswordInput({ style, containerStyle, className, ...props }) {
    const [show, setShow] = useState(false);
    return (
        <div style={{ position: 'relative', width: '100%', ...containerStyle }}>
            <input
                {...props}
                type={show ? 'text' : 'password'}
                className={className}
                // Password managers (NortonLifeLock, 1Password, LastPass, …) inject
                // their own attributes — e.g. data-nlok-ref-guid — into credential
                // fields BEFORE React hydrates, which surfaces as a hydration
                // mismatch error overlay on the login screen. The markup we render
                // is identical on both sides; the difference is entirely the
                // extension's. Suppressing here is the documented remedy and is
                // scoped to this one element, so genuine mismatches elsewhere are
                // still reported.
                suppressHydrationWarning
                style={{ ...style, width: '100%', paddingRight: '2.6rem', boxSizing: 'border-box' }}
            />
            <button
                type="button"
                onClick={() => setShow((s) => !s)}
                aria-label={show ? 'Hide password' : 'Show password'}
                title={show ? 'Hide password' : 'Show password'}
                tabIndex={-1}
                style={{
                    position: 'absolute', right: 8, top: '50%', transform: 'translateY(-50%)',
                    background: 'transparent', border: 'none', cursor: 'pointer',
                    fontSize: '0.95rem', padding: '2px 4px', lineHeight: 1, opacity: 0.75,
                }}
            >
                {show ? '🙈' : '👁️'}
            </button>
        </div>
    );
}
