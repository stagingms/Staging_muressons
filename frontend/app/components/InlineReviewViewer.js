'use client';

import { useState, useMemo } from 'react';
import { sanitizeHtml } from '@/app/utils/sanitize';

/**
 * In-game review/study content viewer.
 * Props: { isOpen, onClose, title, content (markdown-style string) }
 */
export default function InlineReviewViewer({ isOpen, onClose, title, content = '' }) {
  const [isRead, setIsRead] = useState(false);

  // Simple markdown-to-HTML conversion
  const htmlContent = useMemo(() => {
    if (!content) return '';
    return content
      // Headers
      .replace(/^### (.+)$/gm, '<h4 style="font-size:0.95rem;font-weight:700;color:#1e293b;margin:18px 0 8px;border-bottom:1px solid #f1f5f9;padding-bottom:4px">$1</h4>')
      .replace(/^## (.+)$/gm, '<h3 style="font-size:1.15rem;font-weight:700;color:#0f172a;margin:24px 0 10px">$1</h3>')
      // Bold
      .replace(/\*\*(.+?)\*\*/g, '<strong style="color:#4f46e5;font-weight:600">$1</strong>')
      // List items
      .replace(/^- (.+)$/gm, '<li style="margin:3px 0;font-size:0.85rem;color:#334155;line-height:1.5">$1</li>')
      // Numbered list items
      .replace(/^(\d+)\. (.+)$/gm, '<li style="margin:3px 0;font-size:0.85rem;color:#334155;line-height:1.5;list-style-type:decimal">$2</li>')
      // Wrap consecutive li's in ul/ol (simplified)
      .replace(/((?:<li[^>]*>.*<\/li>\n?)+)/g, '<ul style="margin:4px 0 12px 16px;padding:0">$1</ul>')
      // Paragraphs (lines that aren't already HTML)
      .replace(/^(?!<[hulo])((?!<).+)$/gm, '<p style="font-size:0.85rem;color:#475569;line-height:1.6;margin:6px 0">$1</p>')
      // Line breaks
      .replace(/\n\n/g, '<div style="height:8px"></div>');
  }, [content]);

  if (!isOpen) return null;

  return (
    <div style={{
      position: 'fixed', inset: 0, zIndex: 10000,
      background: 'rgba(0,0,0,0.6)', backdropFilter: 'blur(6px)',
      display: 'flex', alignItems: 'center', justifyContent: 'center',
      fontFamily: "'DM Sans', sans-serif",
    }} onClick={onClose}>
      <div style={{
        width: 620, maxHeight: '88vh', borderRadius: 20,
        background: '#fff', boxShadow: '0 25px 60px rgba(0,0,0,0.2)',
        display: 'flex', flexDirection: 'column', overflow: 'hidden',
      }} onClick={e => e.stopPropagation()}>

        {/* Header */}
        <div style={{
          padding: '18px 24px',
          background: 'linear-gradient(135deg, #059669, #0d9488)',
          display: 'flex', alignItems: 'center', justifyContent: 'space-between',
        }}>
          <div>
            <div style={{ fontSize: '0.65rem', color: 'rgba(255,255,255,0.7)', fontWeight: 600, textTransform: 'uppercase', letterSpacing: 1 }}>
              📝 Study Review
            </div>
            <div style={{ fontSize: '1rem', fontWeight: 700, color: '#fff', marginTop: 2 }}>{title}</div>
          </div>
          <button onClick={onClose} style={{
            background: 'rgba(255,255,255,0.2)', border: 'none', borderRadius: 10,
            width: 32, height: 32, color: '#fff', fontSize: '1rem', cursor: 'pointer',
          }}>✕</button>
        </div>

        {/* Content */}
        <div style={{
          flex: 1, overflowY: 'auto', padding: '20px 28px',
        }}>
          <div dangerouslySetInnerHTML={{ __html: sanitizeHtml(htmlContent) }} />
        </div>

        {/* Footer */}
        <div style={{
          padding: '14px 24px', borderTop: '1px solid #f1f5f9',
          display: 'flex', alignItems: 'center', justifyContent: 'space-between',
        }}>
          <div style={{ fontSize: '0.75rem', color: '#94a3b8' }}>
            {isRead ? '✅ Marked as read' : 'Mark this review as completed'}
          </div>
          <button
            onClick={() => setIsRead(true)}
            disabled={isRead}
            style={{
              padding: '8px 20px', borderRadius: 10, border: 'none',
              background: isRead ? '#e2e8f0' : 'linear-gradient(135deg, #059669, #0d9488)',
              color: isRead ? '#94a3b8' : '#fff', fontWeight: 600, cursor: isRead ? 'default' : 'pointer',
              fontSize: '0.82rem',
            }}
          >
            {isRead ? '✓ Completed' : '📖 Mark as Read'}
          </button>
        </div>
      </div>
    </div>
  );
}
