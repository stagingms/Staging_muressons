'use client';
import { useState, useEffect, useCallback, useRef } from 'react';
import { createPortal } from 'react-dom';

/**
 * GlobalTooltip — portal-based tooltip that renders at document.body level.
 * Uses mouseover/mouseout (which bubble) for reliable event delegation on [data-tooltip].
 * Escapes all parent overflow constraints. Mount once in layout.js.
 *
 * Design: premium glassmorphic card with accent left-border, paragraph splitting,
 * full 4-edge viewport clamping, and smooth scale+fade entrance.
 */
export default function GlobalTooltip() {
    const [mounted, setMounted] = useState(false);
    const [visible, setVisible] = useState(false);
    const [text, setText] = useState('');
    const [pos, setPos] = useState({ x: 0, y: 0 });
    const [placement, setPlacement] = useState('above');
    const [arrowOffset, setArrowOffset] = useState(0); // px offset from center after clamping
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

        if (activeElRef.current === el && visible) return;

        clearTimeout(timerRef.current);
        activeElRef.current = el;

        const rect = el.getBoundingClientRect();
        const tooltipHeight = 160;
        const spaceAbove = rect.top;
        const prefersBelow = el.getAttribute('data-tooltip-pos') === 'below';

        let place = 'above';
        if (prefersBelow || spaceAbove < tooltipHeight) {
            place = 'below';
        }

        const x = rect.left + rect.width / 2;
        const y = place === 'above' ? rect.top - 12 : rect.bottom + 12;

        setText(tip);
        setPos({ x, y });
        setPlacement(place);
        setArrowOffset(0);

        timerRef.current = setTimeout(() => setVisible(true), 180);
    }, [visible]);

    const handleOut = useCallback((e) => {
        const target = e.target;
        if (!target || typeof target.closest !== 'function') return;
        const el = target.closest('[data-tooltip]');

        const related = e.relatedTarget;
        if (related && typeof related.closest === 'function') {
            const relatedEl = related.closest('[data-tooltip]');
            if (relatedEl && relatedEl === el) return;
        }

        clearTimeout(timerRef.current);
        setVisible(false);
        activeElRef.current = null;
    }, []);

    useEffect(() => {
        if (!mounted) return;
        document.addEventListener('mouseover', show);
        document.addEventListener('mouseout', handleOut);
        const hideOnScroll = () => {
            clearTimeout(timerRef.current);
            setVisible(false);
            activeElRef.current = null;
        };
        document.addEventListener('scroll', hideOnScroll, true);

        return () => {
            document.removeEventListener('mouseover', show);
            document.removeEventListener('mouseout', handleOut);
            document.removeEventListener('scroll', hideOnScroll, true);
            clearTimeout(timerRef.current);
        };
    }, [mounted, show, handleOut]);

    // Full 4-edge viewport clamping after render, track arrow offset for repositioning
    useEffect(() => {
        if (!visible || !tooltipRef.current) return;
        const rect = tooltipRef.current.getBoundingClientRect();
        const vw = window.innerWidth;
        const vh = window.innerHeight;
        const PAD = 14;
        const LEFT_MIN = PAD;

        let dx = 0;
        if (rect.right > vw - PAD) dx = -(rect.right - vw + PAD);
        if (rect.left + dx < LEFT_MIN) dx = LEFT_MIN - rect.left;

        let dy = 0;
        if (placement === 'above' && rect.top < PAD) dy = PAD - rect.top;
        if (placement === 'below' && rect.bottom > vh - PAD) dy = vh - PAD - rect.bottom;

        if (dx !== 0) {
            setPos(p => ({ ...p, x: p.x + dx }));
            setArrowOffset(-dx); // counter-shift arrow so it still points at the trigger
        }
        if (dy !== 0) {
            setPos(p => ({ ...p, y: p.y + dy }));
        }
    }, [visible, text, placement]);

    if (!mounted) return null;

    const isLight = document.documentElement.getAttribute('data-theme') === 'light';

    // Theme tokens
    const bg          = isLight ? 'rgba(255,255,255,0.97)' : 'rgba(10,15,30,0.96)';
    const fg          = isLight ? '#1e293b' : '#e2e8f0';
    const borderColor = isLight ? 'rgba(15,23,42,0.10)'    : 'rgba(99,130,246,0.22)';
    const accentColor = '#3b82f6';
    const dividerColor = isLight ? 'rgba(15,23,42,0.07)'   : 'rgba(148,163,184,0.12)';
    const shadow      = isLight
        ? '0 8px 32px rgba(0,0,0,0.10), 0 2px 8px rgba(0,0,0,0.06)'
        : '0 8px 40px rgba(0,0,0,0.55), 0 2px 10px rgba(0,0,0,0.35), inset 0 1px 0 rgba(255,255,255,0.05)';

    const isAbove = placement === 'above';

    const tooltipStyle = {
        position: 'fixed',
        zIndex: 999999,
        left: `${pos.x}px`,
        top: isAbove ? 'auto' : `${pos.y}px`,
        bottom: isAbove ? `${window.innerHeight - pos.y}px` : 'auto',
        transform: visible ? 'translateX(-50%) scale(1)' : 'translateX(-50%) scale(0.96)',
        transformOrigin: isAbove ? 'bottom center' : 'top center',
        maxWidth: '360px',
        minWidth: '160px',
        width: 'max-content',
        background: bg,
        backdropFilter: 'blur(28px) saturate(1.6)',
        WebkitBackdropFilter: 'blur(28px) saturate(1.6)',
        // Use per-side longhands only — mixing the `border` shorthand with a
        // `borderLeft` longhand makes React warn about conflicting style props
        // on rerender. Same look: 1px on three sides, 3px accent on the left.
        borderTop: `1px solid ${borderColor}`,
        borderRight: `1px solid ${borderColor}`,
        borderBottom: `1px solid ${borderColor}`,
        borderLeft: `3px solid ${accentColor}`,
        borderRadius: '10px',
        boxShadow: shadow,
        fontFamily: 'var(--font-sans, system-ui, -apple-system, sans-serif)',
        fontSize: '0.76rem',
        fontWeight: 500,
        lineHeight: 1.6,
        letterSpacing: '0.015em',
        color: fg,
        pointerEvents: 'none',
        opacity: visible ? 1 : 0,
        transition: 'opacity 0.18s cubic-bezier(0.23,1,0.32,1), transform 0.18s cubic-bezier(0.23,1,0.32,1)',
        overflow: 'hidden',
    };

    // Arrow caret — shifts with arrowOffset so it stays over the trigger element
    const arrowStyle = {
        position: 'absolute',
        left: `calc(50% + ${arrowOffset}px)`,
        transform: 'translateX(-50%)',
        width: 0,
        height: 0,
        borderWidth: '6px',
        borderStyle: 'solid',
        borderTopColor:    isAbove ? accentColor : 'transparent',
        borderBottomColor: isAbove ? 'transparent' : accentColor,
        borderLeftColor:  'transparent',
        borderRightColor: 'transparent',
        ...(isAbove ? { bottom: '-11px' } : { top: '-11px' }),
    };

    // Split text on double-newline into structured paragraphs
    const renderContent = () => {
        const paragraphs = text.split(/\n\n+/).map(p => p.trim()).filter(Boolean);

        if (paragraphs.length <= 1) {
            return (
                <div style={{ padding: '11px 14px', color: fg }}>
                    {text}
                </div>
            );
        }

        return (
            <div>
                {paragraphs.map((para, i) => {
                    const isFirst    = i === 0;
                    const isAnswers  = para.startsWith('Answers:');
                    const isTag      = para.startsWith('Tag:');
                    const isMsg      = para.startsWith('📨');
                    const isDanger   = para.startsWith('Danger Level:') || para.startsWith('Parameters:');

                    let paraColor  = isFirst ? fg : (isLight ? '#475569' : '#94a3b8');
                    let paraWeight = isFirst ? 600 : 400;
                    let paraSize   = isFirst ? '0.78rem' : '0.74rem';

                    if (isAnswers) { paraColor = isLight ? '#2563eb' : '#93c5fd'; paraWeight = 500; }
                    if (isTag)     { paraColor = isLight ? '#7c3aed' : '#c4b5fd'; paraWeight = 700; paraSize = '0.7rem'; }
                    if (isMsg)     { paraColor = isLight ? '#0369a1' : '#7dd3fc'; paraWeight = 600; }
                    if (isDanger)  { paraColor = isLight ? '#92400e' : '#fbbf24'; paraWeight = 500; paraSize = '0.72rem'; }

                    return (
                        <div
                            key={i}
                            style={{
                                padding: isFirst ? '11px 14px 9px' : '7px 14px',
                                borderTop: i > 0 ? `1px solid ${dividerColor}` : 'none',
                                color: paraColor,
                                fontSize: paraSize,
                                fontWeight: paraWeight,
                                fontStyle: isAnswers ? 'italic' : 'normal',
                            }}
                        >
                            {isTag ? (
                                <span style={{
                                    display: 'inline-flex',
                                    alignItems: 'center',
                                    background: isLight ? 'rgba(124,58,237,0.08)' : 'rgba(196,181,253,0.10)',
                                    border: `1px solid ${isLight ? 'rgba(124,58,237,0.2)' : 'rgba(196,181,253,0.2)'}`,
                                    borderRadius: '4px',
                                    padding: '2px 8px',
                                    fontSize: '0.68rem',
                                    fontWeight: 700,
                                    letterSpacing: '0.07em',
                                    textTransform: 'uppercase',
                                    color: paraColor,
                                }}>
                                    🏷 {para.replace('Tag: ', '')}
                                </span>
                            ) : para}
                        </div>
                    );
                })}
            </div>
        );
    };

    return createPortal(
        <div ref={tooltipRef} style={tooltipStyle}>
            <div style={arrowStyle} />
            {renderContent()}
        </div>,
        document.body
    );
}
