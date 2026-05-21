'use client';
import { useState, useEffect, useCallback } from 'react';

/**
 * GlossaryManager — God Mode admin panel for managing glossary terms.
 * Supports add, edit, delete with weblink field.
 */

const API = process.env.NEXT_PUBLIC_API_URL || '';

export default function GlossaryManager() {
  const [terms, setTerms] = useState([]);
  const [loading, setLoading] = useState(true);
  const [editingTerm, setEditingTerm] = useState(null); // null = closed, {} = new, {id:...} = editing
  const [search, setSearch] = useState('');

  const fetchTerms = useCallback(async () => {
    try {
      const res = await fetch(`${API}/api/admin/glossary`);
      const data = await res.json();
      setTerms(data.terms || []);
    } catch (e) { console.error('Failed to fetch glossary', e); }
    setLoading(false);
  }, []);

  useEffect(() => { fetchTerms(); }, [fetchTerms]);

  const saveTerm = async (item) => {
    try {
      await fetch(`${API}/api/admin/glossary`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(item),
      });
      setEditingTerm(null);
      fetchTerms();
    } catch (e) { console.error('Save failed', e); }
  };

  const deleteTerm = async (termId) => {
    if (!confirm('Delete this term?')) return;
    try {
      await fetch(`${API}/api/admin/glossary/${termId}`, { method: 'DELETE' });
      fetchTerms();
    } catch (e) { console.error('Delete failed', e); }
  };

  const filtered = search.trim()
    ? terms.filter(t =>
        t.term.toLowerCase().includes(search.toLowerCase()) ||
        t.definition.toLowerCase().includes(search.toLowerCase()) ||
        (t.tags || []).some(tag => tag.toLowerCase().includes(search.toLowerCase()))
      )
    : terms;

  return (
    <div>
      <div style={{
        display: 'flex', alignItems: 'center', justifyContent: 'space-between',
        marginBottom: 16, gap: 12, flexWrap: 'wrap',
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
          <span style={{ fontSize: '1.3rem' }}>📖</span>
          <h3 style={{ margin: 0, fontSize: '1rem', fontWeight: 800, color: 'var(--text-primary)' }}>
            Glossary Manager
          </h3>
          <span style={{
            fontSize: '0.6rem', fontWeight: 700, background: 'rgba(99,102,241,0.12)',
            color: '#818cf8', padding: '2px 8px', borderRadius: 10,
          }}>{terms.length} terms</span>
        </div>
        <button
          onClick={() => setEditingTerm({ id: '', term: '', definition: '', tags: [], weblink: '' })}
          style={{
            background: 'linear-gradient(135deg, #6366f1, #8b5cf6)',
            color: '#fff', border: 'none', borderRadius: 8,
            padding: '6px 14px', fontSize: '0.72rem', fontWeight: 700,
            cursor: 'pointer', display: 'flex', alignItems: 'center', gap: 4,
          }}
        >
          ➕ Add Term
        </button>
      </div>

      {/* Search */}
      <input
        type="text"
        placeholder="🔍 Filter terms..."
        value={search}
        onChange={e => setSearch(e.target.value)}
        style={{
          width: '100%', padding: '8px 12px', borderRadius: 8,
          border: '1px solid var(--border-subtle)', fontSize: '0.78rem',
          outline: 'none', fontFamily: 'Inter, sans-serif',
          background: 'var(--bg-body)', color: 'var(--text-primary)',
          marginBottom: 12,
        }}
      />

      {/* Edit Modal */}
      {editingTerm && (
        <EditTermModal
          term={editingTerm}
          onSave={saveTerm}
          onClose={() => setEditingTerm(null)}
        />
      )}

      {/* Terms Table */}
      {loading ? (
        <div style={{ textAlign: 'center', padding: '2rem', color: 'var(--text-muted)', fontSize: '0.8rem' }}>
          Loading glossary...
        </div>
      ) : (
        <div style={{
          maxHeight: 700, overflowY: 'auto',
          borderRadius: 10, border: '1px solid var(--border-subtle)',
        }}>
          <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.75rem' }}>
            <thead>
              <tr style={{ background: 'var(--bg-elevated)', position: 'sticky', top: 0, zIndex: 2 }}>
                <th style={{ ...thStyle, width: 140 }}>Term</th>
                <th style={{ ...thStyle, width: 200 }}>Definition</th>
                <th style={{ ...thStyle, width: 100 }}>Tags</th>
                <th style={{ ...thStyle, width: 50 }}>Link</th>
                <th style={{ ...thStyle, width: 70 }}>Actions</th>
              </tr>
            </thead>
            <tbody>
              {filtered.map(t => (
                <tr key={t.id} style={{ borderBottom: '1px solid var(--border-subtle)' }}>
                  <td style={tdStyle}>
                    <span style={{ fontWeight: 700, color: 'var(--text-primary)' }}>{t.term}</span>
                  </td>
                  <td style={{ ...tdStyle, color: 'var(--text-secondary)', lineHeight: 1.5, maxWidth: 200, fontSize: '0.7rem' }}>
                    {t.definition.length > 100 ? t.definition.slice(0, 100) + '…' : t.definition}
                  </td>
                  <td style={tdStyle}>
                    <div style={{ display: 'flex', gap: 2, flexWrap: 'wrap' }}>
                      {(t.tags || []).slice(0, 3).map(tag => (
                        <span key={tag} style={{
                          background: 'rgba(99,102,241,0.12)', color: '#818cf8',
                          fontSize: '0.68rem', fontWeight: 700,
                          padding: '1px 4px', borderRadius: 3,
                        }}>{tag}</span>
                      ))}
                      {(t.tags || []).length > 3 && (
                        <span style={{ fontSize: '0.68rem', color: 'var(--text-muted)' }}>+{t.tags.length - 3}</span>
                      )}
                    </div>
                  </td>
                  <td style={tdStyle}>
                    {t.weblink ? (
                      <a href={t.weblink} target="_blank" rel="noopener noreferrer"
                         style={{ color: '#818cf8', fontSize: '0.85rem' }}
                         title={t.weblink}>🔗</a>
                    ) : (
                      <span style={{ color: 'var(--text-muted)' }}>—</span>
                    )}
                  </td>
                  <td style={tdStyle}>
                    <div style={{ display: 'flex', gap: 4 }}>
                      <button
                        onClick={() => setEditingTerm(t)}
                        style={actionBtnStyle}
                        title="Edit"
                      >✏️</button>
                      <button
                        onClick={() => deleteTerm(t.id)}
                        style={{ ...actionBtnStyle, color: '#ef4444' }}
                        title="Delete"
                      >🗑️</button>
                    </div>
                  </td>
                </tr>
              ))}
              {filtered.length === 0 && (
                <tr>
                  <td colSpan={5} style={{ textAlign: 'center', padding: '1.5rem', color: 'var(--text-muted)', fontSize: '0.78rem' }}>
                    {search ? 'No terms match your filter' : 'No glossary terms yet'}
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}

const thStyle = {
  textAlign: 'left', padding: '8px 10px',
  fontSize: '0.65rem', fontWeight: 700, color: 'var(--text-muted)',
  letterSpacing: '0.04em', textTransform: 'uppercase',
  borderBottom: '1px solid var(--border-subtle)',
};

const tdStyle = {
  padding: '8px 10px', verticalAlign: 'top',
};

const actionBtnStyle = {
  background: 'none', border: 'none',
  cursor: 'pointer', fontSize: '0.75rem', padding: '2px 4px',
};


function EditTermModal({ term, onSave, onClose }) {
  const [form, setForm] = useState({
    id: term.id || '',
    term: term.term || '',
    definition: term.definition || '',
    tags: (term.tags || []).join(', '),
    weblink: term.weblink || '',
  });

  const handleSubmit = (e) => {
    e.preventDefault();
    onSave({
      id: form.id,
      term: form.term.trim(),
      definition: form.definition.trim(),
      tags: form.tags.split(',').map(t => t.trim()).filter(Boolean),
      weblink: form.weblink.trim(),
    });
  };

  const isNew = !term.id;

  return (
    <div style={{
      position: 'fixed', inset: 0, zIndex: 15000,
      background: 'rgba(15,23,42,0.5)', backdropFilter: 'blur(4px)',
      display: 'flex', alignItems: 'center', justifyContent: 'center',
      fontFamily: 'Inter, sans-serif',
    }} onClick={onClose}>
      <div onClick={e => e.stopPropagation()} style={{
        background: 'var(--bg-card)', borderRadius: 14, width: '92%', maxWidth: 480,
        boxShadow: '0 25px 60px rgba(0,0,0,0.3)',
        padding: '1.2rem',
        border: '1px solid var(--border-subtle)',
      }}>
        <h3 style={{ margin: '0 0 12px', fontSize: '0.95rem', fontWeight: 800, color: 'var(--text-primary)' }}>
          {isNew ? '➕ Add New Term' : '✏️ Edit Term'}
        </h3>
        <form onSubmit={handleSubmit}>
          <div style={fieldStyle}>
            <label style={labelStyle}>Term Name *</label>
            <input
              required
              value={form.term}
              onChange={e => setForm({ ...form, term: e.target.value })}
              placeholder="e.g. EBITDA"
              style={inputStyle}
            />
          </div>
          <div style={fieldStyle}>
            <label style={labelStyle}>Definition *</label>
            <textarea
              required
              value={form.definition}
              onChange={e => setForm({ ...form, definition: e.target.value })}
              placeholder="Clear, concise definition..."
              rows={3}
              style={{ ...inputStyle, resize: 'vertical' }}
            />
          </div>
          <div style={fieldStyle}>
            <label style={labelStyle}>Tags <span style={{ fontWeight: 400, color: 'var(--text-muted)' }}>(comma-separated)</span></label>
            <input
              value={form.tags}
              onChange={e => setForm({ ...form, tags: e.target.value })}
              placeholder="e.g. finance, esg, governance"
              style={inputStyle}
            />
          </div>
          <div style={fieldStyle}>
            <label style={labelStyle}>Web Link <span style={{ fontWeight: 400, color: 'var(--text-muted)' }}>(optional)</span></label>
            <input
              value={form.weblink}
              onChange={e => setForm({ ...form, weblink: e.target.value })}
              placeholder="https://example.com/learn-more"
              type="url"
              style={inputStyle}
            />
          </div>
          <div style={{ display: 'flex', gap: 8, justifyContent: 'flex-end', marginTop: 16 }}>
            <button type="button" onClick={onClose} style={{
              padding: '7px 16px', borderRadius: 8, border: '1px solid var(--border-subtle)',
              background: 'var(--bg-body)', color: 'var(--text-muted)', fontSize: '0.75rem',
              fontWeight: 700, cursor: 'pointer',
            }}>Cancel</button>
            <button type="submit" style={{
              padding: '7px 16px', borderRadius: 8, border: 'none',
              background: 'linear-gradient(135deg, #6366f1, #8b5cf6)',
              color: '#fff', fontSize: '0.75rem', fontWeight: 700, cursor: 'pointer',
            }}>{isNew ? 'Add Term' : 'Save Changes'}</button>
          </div>
        </form>
      </div>
    </div>
  );
}

const fieldStyle = { marginBottom: 10 };
const labelStyle = {
  display: 'block', fontSize: '0.68rem', fontWeight: 700,
  color: 'var(--text-secondary)', marginBottom: 3,
};
const inputStyle = {
  width: '100%', padding: '7px 10px', borderRadius: 7,
  border: '1px solid var(--border-subtle)', fontSize: '0.78rem',
  outline: 'none', fontFamily: 'Inter, sans-serif',
  background: 'var(--bg-body)', color: 'var(--text-primary)',
};
