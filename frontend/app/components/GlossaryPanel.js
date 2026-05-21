'use client';
import { useState, useMemo, useRef, useEffect } from 'react';

/**
 * GlossaryPanel — Search-first glossary of financial & ESG terms.
 * Fetches terms from the backend API (managed via God Mode).
 * Shows results only when the player types a query.
 * Related terms appear below the matched result.
 */

const API = process.env.NEXT_PUBLIC_API_URL || '';

// Fallback terms in case API is unreachable
const FALLBACK_TERMS = [
  { id: 'ebitda', term: 'EBITDA', definition: 'Earnings Before Interest, Taxes, Depreciation, and Amortization — measures operational profitability.', tags: ['finance', 'profitability', 'earnings'], weblink: '' },
  { id: 'esg', term: 'ESG', definition: 'Environmental, Social, and Governance — three pillars for measuring corporate sustainability and ethical impact.', tags: ['esg', 'sustainability', 'environment', 'social', 'governance'], weblink: '' },
  { id: 'treasury', term: 'Treasury', definition: 'Corporate cash reserves — main financial health indicator. Depleted by investments, crises, and operating costs.', tags: ['finance', 'cash', 'investment'], weblink: '' },
];

function getRelatedTerms(matchedTerm, allTerms) {
  const matchedTags = new Set(matchedTerm.tags || []);
  return allTerms
    .filter(t => t.term !== matchedTerm.term)
    .map(t => {
      const overlap = (t.tags || []).filter(tag => matchedTags.has(tag)).length;
      return { ...t, overlap };
    })
    .filter(t => t.overlap > 0)
    .sort((a, b) => b.overlap - a.overlap)
    .slice(0, 3);
}

export default function GlossaryPanel({ isOpen, onClose }) {
  const [search, setSearch] = useState('');
  const [allTerms, setAllTerms] = useState([]);
  const [loaded, setLoaded] = useState(false);
  const inputRef = useRef(null);

  // Fetch terms from API
  useEffect(() => {
    if (!isOpen) return;
    setSearch('');
    setLoaded(false);
    (async () => {
      try {
        const res = await fetch(`${API}/api/admin/glossary`);
        const data = await res.json();
        setAllTerms(data.terms || FALLBACK_TERMS);
      } catch {
        setAllTerms(FALLBACK_TERMS);
      }
      setLoaded(true);
      setTimeout(() => inputRef.current?.focus(), 100);
    })();
  }, [isOpen]);

  const matches = useMemo(() => {
    if (!search.trim()) return [];
    const q = search.toLowerCase();
    return allTerms.filter(t =>
      t.term.toLowerCase().includes(q) ||
      t.definition.toLowerCase().includes(q) ||
      (t.tags || []).some(tag => tag.includes(q))
    );
  }, [search, allTerms]);

  if (!isOpen) return null;

  const hasResults = matches.length > 0;

  return (
    <div style={{
      position: 'fixed', inset: 0, zIndex: 12000,
      background: 'rgba(15,23,42,0.5)', backdropFilter: 'blur(4px)',
      display: 'flex', alignItems: 'center', justifyContent: 'center',
      fontFamily: 'Inter, sans-serif',
    }} onClick={onClose}>
      <div onClick={e => e.stopPropagation()} style={{
        background: '#fff', borderRadius: 16, width: '90%', maxWidth: 520,
        maxHeight: '80vh', overflow: 'hidden', display: 'flex', flexDirection: 'column',
        boxShadow: '0 25px 60px rgba(0,0,0,0.2)',
      }}>
        {/* Header */}
        <div style={{
          padding: '1rem 1.2rem', borderBottom: '1px solid #e2e8f0',
          display: 'flex', alignItems: 'center', justifyContent: 'space-between',
        }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
            <span style={{ fontSize: '1.3rem' }}>📖</span>
            <h2 style={{ margin: 0, fontSize: '1.05rem', fontWeight: 800, color: '#0f172a' }}>Glossary</h2>
          </div>
          <button onClick={onClose} style={{
            background: '#f1f5f9', border: 'none', borderRadius: '50%',
            width: 28, height: 28, cursor: 'pointer', fontSize: '0.85rem',
            display: 'flex', alignItems: 'center', justifyContent: 'center',
            color: '#64748b', fontWeight: 700,
          }}>✕</button>
        </div>

        {/* Search */}
        <div style={{ padding: '0.8rem 1.2rem' }}>
          <input
            ref={inputRef}
            type="text"
            placeholder="Search a term... e.g. EBITDA, carbon, treasury"
            value={search}
            onChange={e => setSearch(e.target.value)}
            autoFocus
            style={{
              width: '100%', padding: '10px 14px', borderRadius: 10,
              border: '2px solid #e2e8f0', fontSize: '0.82rem',
              outline: 'none', fontFamily: 'Inter, sans-serif',
              background: '#f8fafc',
              transition: 'border-color 0.2s',
            }}
            onFocus={e => e.target.style.borderColor = '#6366f1'}
            onBlur={e => e.target.style.borderColor = '#e2e8f0'}
          />
        </div>

        {/* Content */}
        <div style={{ overflow: 'auto', flex: 1, padding: '0 1.2rem 1rem' }}>

          {/* Empty state — no search yet */}
          {!search.trim() && (
            <div style={{
              textAlign: 'center', padding: '2.5rem 1rem',
              color: '#94a3b8',
            }}>
              <div style={{ fontSize: '2.5rem', marginBottom: 12 }}>🔍</div>
              <div style={{ fontSize: '0.82rem', fontWeight: 600, color: '#64748b', marginBottom: 4 }}>
                Type to search
              </div>
              <div style={{ fontSize: '0.72rem', lineHeight: 1.6 }}>
                Search by keyword, term name, or topic<br />
                <span style={{ opacity: 0.7 }}>e.g. "carbon", "treasury", "governance"</span>
              </div>
            </div>
          )}

          {/* No results */}
          {search.trim() && !hasResults && (
            <div style={{
              textAlign: 'center', padding: '2rem 1rem',
              color: '#94a3b8',
            }}>
              <div style={{ fontSize: '1.5rem', marginBottom: 8 }}>🤷</div>
              <div style={{ fontSize: '0.78rem', fontWeight: 600, color: '#64748b' }}>
                No matching terms found
              </div>
              <div style={{ fontSize: '0.7rem', marginTop: 4 }}>
                Try a different keyword
              </div>
            </div>
          )}

          {/* Results */}
          {hasResults && matches.map(item => {
            const related = getRelatedTerms(item, allTerms);
            return (
              <div key={item.id || item.term} style={{
                marginBottom: 12,
                background: '#f8fafc', borderRadius: 12,
                border: '1px solid #e2e8f0', overflow: 'hidden',
              }}>
                {/* Main result */}
                <div style={{ padding: '0.8rem 1rem' }}>
                  <div style={{
                    fontSize: '0.82rem', fontWeight: 700, color: '#1e293b',
                    display: 'flex', alignItems: 'center', gap: 6, marginBottom: 5,
                  }}>
                    <span style={{
                      background: 'linear-gradient(135deg, #6366f1, #8b5cf6)',
                      color: '#fff', fontSize: '0.68rem',
                      fontWeight: 800, padding: '2px 6px', borderRadius: 4,
                      letterSpacing: '0.05em',
                    }}>TERM</span>
                    {item.term}
                    {item.weblink && (
                      <a href={item.weblink} target="_blank" rel="noopener noreferrer"
                         style={{ fontSize: '0.75rem', color: '#6366f1', textDecoration: 'none' }}
                         title="Learn more">🔗</a>
                    )}
                  </div>
                  <div style={{ fontSize: '0.74rem', color: '#475569', lineHeight: 1.6 }}>
                    {item.definition}
                  </div>
                </div>

                {/* Related terms */}
                {related.length > 0 && (
                  <div style={{
                    background: '#f1f5f9', padding: '0.5rem 1rem',
                    borderTop: '1px solid #e2e8f0',
                  }}>
                    <div style={{
                      fontSize: '0.68rem', fontWeight: 700, color: '#94a3b8',
                      letterSpacing: '0.08em', textTransform: 'uppercase', marginBottom: 4,
                    }}>Related</div>
                    <div style={{ display: 'flex', gap: 5, flexWrap: 'wrap' }}>
                      {related.map(r => (
                        <button
                          key={r.id || r.term}
                          onClick={() => setSearch(r.term)}
                          style={{
                            background: '#fff', border: '1px solid #e2e8f0',
                            borderRadius: 6, padding: '3px 8px',
                            fontSize: '0.65rem', fontWeight: 600, color: '#6366f1',
                            cursor: 'pointer', transition: 'background 0.15s, color 0.15s, border-color 0.15s, box-shadow 0.15s, opacity 0.15s, transform 0.15s',
                          }}
                          onMouseOver={e => { e.target.style.background = '#eef2ff'; e.target.style.borderColor = '#c7d2fe'; }}
                          onMouseOut={e => { e.target.style.background = '#fff'; e.target.style.borderColor = '#e2e8f0'; }}
                        >
                          {r.term}
                        </button>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
}
