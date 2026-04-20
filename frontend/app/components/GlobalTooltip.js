'use client';
import { useState, useEffect, useCallback, useRef } from 'react';
import { createPortal } from 'react-dom';

/**
 * GlobalTooltip — a portal-based tooltip that renders at document.body level.
 * Uses mouseover/mouseout (which bubble) for reliable event delegation on [data-tooltip].
 * Escapes all parent overflow constraints. Mount once in layout.js.
 */
export default function GlobalTooltip() {
    const [mounted, setMounted] = useState(false);
    const [visible, setVisible] = useState(false);
    const [text, setText] = useState('');
    const [pos, setPos] = useState({ x: 0, y: 0 });
    const [placement, setPlacement] = useState('above');
    const timerRef = useRef(null);
    const activeElRef = useRef(null);
    const tooltipRef = useRef(null);

    useEffect(() => { setMounted(true); }, []);

    const show = useCallback((e) => {
        const target = e.target;
        if (!target || typeof target.closest !== 'function') return;
        const el = target.closest('[data-tooltip]');
        if (!el) return;
        const tip = el.getAttribute('data-tooltip');
        if (!tip) return;

        // Same element — don't restart
        if (activeElRef.current === el && visible) return;

        clearTimeout(timerRef.current);
        activeElRef.current = el;

        const rect = el.getBoundingClientRect();
        const tooltipHeight = 140;
        const spaceAbove = rect.top;
        const prefersBelow = el.getAttribute('data-tooltip-pos') === 'below';

        let place = 'above';
        if (prefersBelow || spaceAbove < tooltipHeight) {
            place = 'below';
        }

        const x = rect.left + rect.width / 2;
        const y = place === 'above' ? rect.top - 10 : rect.bottom + 10;

        setText(tip);
        setPos({ x, y });
        setPlacement(place);

        timerRef.current = setTimeout(() => setVisible(true), 250);
    }, [visible]);

    const handleOut = useCallback((e) => {
        const target = e.target;
        if (!target || typeof target.closest !== 'function') return;
        const el = target.closest('[data-tooltip]');

        // Check if we're moving to a child of the same tooltip trigger
        const related = e.relatedTarget;
        if (related && typeof related.closest === 'function') {
            const relatedEl = related.closest('[data-tooltip]');
            if (relatedEl && relatedEl === el) return; // still inside same trigger
        }

        clearTimeout(timerRef.current);
        setVisible(false);
        activeElRef.current = null;
    }, []);

    useEffect(() => {
        if (!mounted) return;

        // mouseover/mouseout bubble — reliable for delegation
        document.addEventListener('mouseover', show);
        document.addEventListener('mouseout', handleOut);
        document.addEventListener('scroll', () => {
            clearTimeout(timerRef.current);
            setVisible(false);
            activeElRef.current = null;
        }, true);

        return () => {
            document.removeEventListener('mouseover', show);
            document.removeEventListener('mouseout', handleOut);
            clearTimeout(timerRef.current);
        };
    }, [mounted, show, handleOut]);

    // Clamp tooltip position to viewport
    useEffect(() => {
        if (!visible || !tooltipRef.current) return;
        const rect = tooltipRef.current.getBoundingClientRect();
        const vw = window.innerWidth;

        if (rect.right > vw - 12) {
            setPos(p => ({ ...p, x: p.x - (rect.right - vw + 16) }));
        }
        if (rect.left < 12) {
            setPos(p => ({ ...p, x: p.x + (16 - rect.left) }));
        }
    }, [visible, text]);

    if (!mounted) return null;

    // Detect light theme
    const isLight = document.documentElement.getAttribute('data-theme') === 'light';

    const bg = isLight ? 'rgba(255, 255, 255, 0.97)' : 'rgba(8, 12, 24, 0.94)';
    const fg = isLight ? '#1e293b' : '#e2e8f0';
    const borderColor = isLight ? 'rgba(15, 23, 42, 0.1)' : 'rgba(59, 130, 246, 0.2)';
    const shadow = isLight
        ? '0 12px 40px rgba(0,0,0,0.1), 0 4px 12px rgba(0,0,0,0.06), inset 0 1px 0 rgba(255,255,255,0.9)'
        : '0 12px 40px rgba(0,0,0,0.5), 0 4px 12px rgba(0,0,0,0.3), inset 0 1px 0 rgba(255,255,255,0.06)';

    const tooltipStyle = {
        position: 'fixed',
        zIndex: 999999,
        left: `${pos.x}px`,
        top: placement === 'above' ? 'auto' : `${pos.y}px`,
        bottom: placement === 'above' ? `${window.innerHeight - pos.y}px` : 'auto',
        transform: 'translateX(-50%)',
        maxWidth: '400px',
        width: 'max-content',
        padding: '14px 18px',
        background: bg,
        backdropFilter: 'blur(24px) saturate(1.5)',
        WebkitBackdropFilter: 'blur(24px) saturate(1.5)',
        border: `1px solid ${borderColor}`,
        borderRadius: '12px',
        boxShadow: shadow,
        fontFamily: 'var(--font-sans)',
        fontSize: '0.8rem',
        fontWeight: 420,
        lineHeight: 1.6,
        letterSpacing: '0.01em',
        color: fg,
        textAlign: 'left',
        wordBreak: 'break-word',
        opacity: visible ? 1 : 0,
        pointerEvents: 'none',
        transition: 'opacity 0.2s cubic-bezier(0.23,1,0.32,1)',
    };

    const arrowStyle = {
        position: 'absolute',
        left: '50%',
        transform: 'translateX(-50%)',
        width: 0,
        height: 0,
        border: '7px solid transparent',
    };

    if (placement === 'above') {
        arrowStyle.bottom = '-13px';
        arrowStyle.borderTopColor = bg;
    } else {
        arrowStyle.top = '-13px';
        arrowStyle.borderBottomColor = bg;
    }

    // Split text on "Answers:" to render it as a distinct styled line
    const renderText = () => {
        const idx = text.indexOf('Answers:');
        if (idx === -1) return text;

        const main = text.slice(0, idx).trim();
        const question = text.slice(idx).trim();

        return (
            <>
                <span>{main}</span>
                <span style={{
                    display: 'block',
                    marginTop: '8px',
                    paddingTop: '7px',
                    borderTop: `1px solid ${isLight ? 'rgba(15,23,42,0.08)' : 'rgba(148,163,184,0.15)'}`,
                    color: isLight ? '#2563eb' : '#93c5fd',
                    fontWeight: 500,
                    fontStyle: 'italic',
                    fontSize: '0.78rem',
                }}>
                    {question}
                </span>
            </>
        );
    };

    return createPortal(
        <div ref={tooltipRef} style={tooltipStyle}>
            <div style={arrowStyle} />
            {renderText()}
        </div>,
        document.body
    );
}
