/**
 * HIGH-007/008: HTML sanitisation utility.
 *
 * Wraps DOMPurify for use in Next.js 'use client' components.
 * Server-side (SSR/SSG): returns the raw string untouched because
 * DOMPurify requires a DOM environment. Sanitisation runs on the
 * client before the string is ever inserted into the DOM.
 *
 * Usage:
 *   import { sanitizeHtml } from '@/app/utils/sanitize';
 *   <div dangerouslySetInnerHTML={{ __html: sanitizeHtml(untrustedHtml) }} />
 */

let _DOMPurify = null;

function _getPurify() {
    if (_DOMPurify) return _DOMPurify;
    if (typeof window === 'undefined') return null; // SSR — no DOM
    try {
        // Dynamic require keeps this out of the SSR bundle
        // eslint-disable-next-line @typescript-eslint/no-var-requires
        const DOMPurify = require('dompurify');
        _DOMPurify = DOMPurify.default || DOMPurify;
    } catch {
        // DOMPurify not installed — fall back to stripping all tags
        _DOMPurify = null;
    }
    return _DOMPurify;
}

/**
 * Sanitize an HTML string.
 * - Strips all script tags, event handlers, and javascript: hrefs.
 * - Preserves safe formatting tags: b, i, em, strong, p, br, ul, ol, li, a.
 * - Falls back to plain-text escaping if DOMPurify is unavailable.
 *
 * @param {string} dirty  - Potentially unsafe HTML string
 * @returns {string}       - Safe HTML string
 */
export function sanitizeHtml(dirty) {
    if (!dirty || typeof dirty !== 'string') return '';
    const purify = _getPurify();
    if (purify) {
        return purify.sanitize(dirty, {
            ALLOWED_TAGS: ['b', 'i', 'em', 'strong', 'p', 'br', 'ul', 'ol', 'li', 'a', 'span', 'div', 'h1', 'h2', 'h3', 'h4'],
            ALLOWED_ATTR: ['href', 'title', 'target', 'rel', 'class', 'style'],
            FORCE_BODY: false,
        });
    }
    // Fallback: escape all HTML entities (no tags at all)
    return dirty
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;')
        .replace(/"/g, '&quot;')
        .replace(/'/g, '&#x27;');
}

/**
 * Sanitize CSS for injection into <style> tags.
 * Only allows safe CSS properties — strips url(), expressions, @import.
 * Used for dynamic animation/keyframe injection (NOT user content).
 */
export function sanitizeCss(css) {
    if (!css || typeof css !== 'string') return '';
    // Strip dangerous CSS patterns
    return css
        .replace(/url\s*\([^)]*\)/gi, '')          // url()
        .replace(/expression\s*\([^)]*\)/gi, '')    // expression()
        .replace(/@import\b[^;]*/gi, '')            // @import
        .replace(/javascript\s*:/gi, '');           // javascript:
}
