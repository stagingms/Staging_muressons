'use client';

/**
 * Dialog — the ONE modal-accessibility primitive (UX audit #18, WCAG 2.1 AA).
 *
 * WHY THIS EXISTS
 *   The 2026-08-02 UX audit found 6 of 8 modals with no `role="dialog"`, no
 *   `aria-modal`, no Escape handling, no focus trap and no focus restore —
 *   including JoinCohortModal, the first screen every participant sees. That
 *   is a 4.1.2 / 2.4.3 / 2.1.2 failure on a product with a CONTRACTUAL WCAG
 *   requirement. `ConfirmModal` already had most of the behaviour; this
 *   extracts it so there is one implementation instead of eight.
 *
 * DESIGN CONSTRAINT — this is a WRAPPER, not a redesign.
 *   It renders the overlay element and owns the a11y behaviour; every caller
 *   keeps its own className, inline styles and inner markup exactly as-is.
 *   Adopting it is a two-line change per modal and cannot alter layout.
 *
 *   Before:  <div className={styles.overlay}> …panel… </div>
 *   After:   <Dialog className={styles.overlay} onClose={fn} label="…"> …panel… </Dialog>
 *
 * WHAT IT GUARANTEES
 *   • role="dialog" + aria-modal="true" + an accessible name (2.4.6 / 4.1.2)
 *   • Escape closes — but ONLY the topmost dialog (module-level stack), so a
 *     nested dialog (JoinCohort → ChangePassword) doesn't collapse both.
 *   • Focus moves into the dialog on open — to `initialFocusRef` if given,
 *     else the first focusable node, else the dialog itself.
 *   • Tab / Shift+Tab cycle WITHIN the dialog (2.1.2, no keyboard trap escape
 *     to the page behind).
 *   • Focus returns to whatever was focused before opening (2.4.3).
 *   • Background scroll is locked while open, refcounted so nested dialogs
 *     don't unlock early.
 *
 * ESCAPE HATCHES
 *   `dismissible={false}` for a modal the user must resolve (forced password
 *   change) — suppresses Escape and backdrop-click but keeps every other
 *   guarantee. Never use it to trap someone with no way out: provide a button.
 */

import { useEffect, useRef, useCallback, useId } from 'react';

// Module-level stack so only the TOP dialog reacts to Escape.
const _stack = [];
// Refcount so nested dialogs don't restore scroll while one is still open.
let _scrollLocks = 0;
let _prevOverflow = null;

const FOCUSABLE = [
    'a[href]', 'button:not([disabled])', 'input:not([disabled]):not([type="hidden"])',
    'select:not([disabled])', 'textarea:not([disabled])',
    '[tabindex]:not([tabindex="-1"])',
].join(',');

export default function Dialog({
    children,
    onClose,
    /** Accessible name. Use `label` for a plain string, or `labelledBy` for an
     *  existing heading's id when the modal already renders its own title. */
    label,
    labelledBy,
    describedBy,
    /** Passed straight through to the overlay element — callers keep their styling. */
    className,
    style,
    /** Focus this element on open instead of the first focusable node. */
    initialFocusRef,
    /** false = Escape and backdrop-click are disabled (forced/blocking modals). */
    dismissible = true,
    /** Close when the backdrop itself is clicked (ignored if !dismissible). */
    closeOnBackdrop = true,
    /** Escape hatch for callers that must reach the overlay node. */
    overlayRef,
    ...rest
}) {
    const innerRef = useRef(null);
    const restoreRef = useRef(null);
    const autoId = useId();
    const titleId = labelledBy || undefined;

    const setRefs = useCallback((node) => {
        innerRef.current = node;
        if (overlayRef) overlayRef.current = node;
    }, [overlayRef]);

    // ── Register on the stack; capture + restore focus; lock scroll ──
    useEffect(() => {
        const token = { id: autoId, onClose, dismissible };
        _stack.push(token);

        restoreRef.current = typeof document !== 'undefined' ? document.activeElement : null;

        if (_scrollLocks === 0 && typeof document !== 'undefined') {
            _prevOverflow = document.body.style.overflow;
            document.body.style.overflow = 'hidden';
        }
        _scrollLocks += 1;

        // Move focus in. rAF so the node is laid out (and any autoFocus has run).
        const raf = requestAnimationFrame(() => {
            const node = innerRef.current;
            if (!node) return;
            const target =
                (initialFocusRef && initialFocusRef.current) ||
                node.querySelector(FOCUSABLE) ||
                node;
            try { target.focus({ preventScroll: true }); } catch { /* non-focusable */ }
        });

        return () => {
            cancelAnimationFrame(raf);
            const i = _stack.indexOf(token);
            if (i !== -1) _stack.splice(i, 1);

            _scrollLocks = Math.max(0, _scrollLocks - 1);
            if (_scrollLocks === 0 && typeof document !== 'undefined') {
                document.body.style.overflow = _prevOverflow || '';
                _prevOverflow = null;
            }

            // 2.4.3: return focus where it came from, if that node still exists.
            const prev = restoreRef.current;
            if (prev && typeof prev.focus === 'function' && document.contains(prev)) {
                try { prev.focus({ preventScroll: true }); } catch { /* gone */ }
            }
        };
        // onClose/dismissible are read live via the stack token below, so this
        // effect intentionally runs once per mount.
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, []);

    // Keep the stack token's handlers current without re-running the mount effect.
    useEffect(() => {
        const token = _stack.find((t) => t.id === autoId);
        if (token) { token.onClose = onClose; token.dismissible = dismissible; }
    }, [autoId, onClose, dismissible]);

    // ── Escape (topmost only) + Tab cycling ──
    useEffect(() => {
        const onKeyDown = (e) => {
            if (e.key === 'Escape') {
                const top = _stack[_stack.length - 1];
                if (!top || top.id !== autoId) return;      // not the topmost
                if (!top.dismissible) return;
                e.stopPropagation();
                e.preventDefault();
                top.onClose?.();
                return;
            }

            if (e.key !== 'Tab') return;
            const top = _stack[_stack.length - 1];
            if (!top || top.id !== autoId) return;
            const node = innerRef.current;
            if (!node) return;

            const items = Array.from(node.querySelectorAll(FOCUSABLE))
                .filter((el) => el.offsetParent !== null || el === document.activeElement);
            if (items.length === 0) {
                // Nothing focusable inside — keep focus on the dialog itself
                // rather than letting Tab escape to the page behind (2.1.2).
                e.preventDefault();
                try { node.focus({ preventScroll: true }); } catch { /* noop */ }
                return;
            }

            const first = items[0];
            const last = items[items.length - 1];
            const active = document.activeElement;

            if (!node.contains(active)) {
                e.preventDefault();
                (e.shiftKey ? last : first).focus();
                return;
            }
            if (e.shiftKey && active === first) {
                e.preventDefault();
                last.focus();
            } else if (!e.shiftKey && active === last) {
                e.preventDefault();
                first.focus();
            }
        };

        window.addEventListener('keydown', onKeyDown, true);
        return () => window.removeEventListener('keydown', onKeyDown, true);
    }, [autoId]);

    const handleClick = (e) => {
        if (!dismissible || !closeOnBackdrop) return;
        if (e.target === e.currentTarget) onClose?.();
    };

    return (
        <div
            ref={setRefs}
            className={className}
            style={style}
            role="dialog"
            aria-modal="true"
            {...(titleId ? { 'aria-labelledby': titleId } : { 'aria-label': label || 'Dialog' })}
            {...(describedBy ? { 'aria-describedby': describedBy } : {})}
            tabIndex={-1}
            onClick={handleClick}
            {...rest}
        >
            {children}
        </div>
    );
}
