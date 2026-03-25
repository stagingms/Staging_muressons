'use client';
import { useState, useRef, useEffect } from 'react';

/**
 * AIAdvisor — AI Strategic Advisor chat panel.
 * Improvement #4.1: AI-powered strategic advisor
 */

const PRESET_PROMPTS = [
  '📋 Explain this round\'s crisis',
  '⚖️ Compare Option A vs B vs C',
  '📊 What happened last round?',
  '💡 How should I allocate capital?',
  '🌱 How to improve my ESG score?',
];

export default function AIAdvisor({ roundNumber, globalState, roundConfig, isOpen, onClose }) {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const scrollRef = useRef(null);

  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [messages]);

  // Initialize with welcome message
  useEffect(() => {
    if (isOpen && messages.length === 0) {
      setMessages([{
        role: 'assistant',
        content: `👋 Hello, CSO. I'm your Strategic Advisor for Round ${roundNumber}. Ask me about the current crisis, compare strategic options, or get capital allocation advice. What would you like to know?`,
      }]);
    }
  }, [isOpen]);

  const generateResponse = (query) => {
    const q = query.toLowerCase();
    const treasury = globalState?.corporate_treasury || 50_000_000;
    const reputation = globalState?.group_reputation || 50;
    const options = roundConfig?.options || {};
    const crisis = roundConfig?.crisis;

    if (q.includes('crisis') || q.includes('explain') || q.includes('round')) {
      return `**Round ${roundNumber} Crisis:**\n\n${crisis?.description || crisis?.narrative || 'The board demands strategic action this quarter.'}\n\n**Key Considerations:**\n• Current Treasury: $${(treasury / 1_000_000).toFixed(1)}M\n• Reputation Score: ${reputation}/100\n• Weigh short-term costs vs long-term resilience`;
    }

    if (q.includes('compare') || q.includes('option') || q.includes('vs')) {
      const opts = Object.entries(options);
      if (opts.length === 0) return 'No strategic options configured for this round. Please wait for the facilitator to load the round configuration.';
      let response = '**Strategic Options Comparison:**\n\n';
      opts.forEach(([key, opt]) => {
        const label = key === 'option_a' ? 'Option A' : key === 'option_b' ? 'Option B' : 'Option C';
        response += `**${label}: ${opt.title}**\n${opt.description}\n`;
        if (opt.impacts?.treasury || opt.cost_impact) {
          response += `Cost Impact: $${((opt.impacts?.treasury || opt.cost_impact) / 1_000_000).toFixed(1)}M\n`;
        }
        response += '\n';
      });
      response += `**My Recommendation:** `;
      if (treasury < 35_000_000) response += `Given your low treasury ($${(treasury / 1_000_000).toFixed(1)}M), consider a cost-conservative option.`;
      else if (reputation < 40) response += `Your reputation is low (${reputation}/100). Prioritize options that boost stakeholder trust.`;
      else response += `You have healthy metrics. Consider investing in long-term resilience for compounding benefits.`;
      return response;
    }

    if (q.includes('allocat') || q.includes('capital') || q.includes('invest')) {
      return `**Capital Allocation Advice:**\n\nYour CSF Pool is 20% of treasury = $${(treasury * 0.2 / 1_000_000).toFixed(1)}M\n\n**Recommended Strategy:**\n• **Pharma** (highest revenue): Allocate 30-35% — strong ROI potential\n• **Electronics** (high carbon): Allocate 25-30% — needs ESG investment\n• **Consumer Goods** (stable): Allocate 20% — steady returns\n• **Software** (lean, low carbon): Allocate 15-20% — already efficient\n\n💡 *Tip: Over-investing in one BU creates concentration risk. Spread your bets.*`;
    }

    if (q.includes('esg') || q.includes('score') || q.includes('improve')) {
      return `**Improving Your ESG Performance:**\n\n📊 Current Score: Reputation ${reputation}/100\n\n**Quick Wins:**\n1. Choose strategic options that reduce carbon intensity\n2. Invest in high-carbon BUs (Electronics, Consumer Goods)\n3. Complete CSRD assessments thoroughly\n4. Avoid CFO overrides (reputation penalty)\n\n**Long-term:**\n• Build social license scores across all BUs\n• Reduce water dependency for Pharma\n• Maintain governance risk below 15 in all units`;
    }

    if (q.includes('last round') || q.includes('previous') || q.includes('happened')) {
      if (roundNumber <= 1) return 'This is Round 1 — no previous round data available yet. Focus on setting a strong foundation!';
      return `**Round ${roundNumber - 1} Summary:**\n\nYour current metrics reflect your cumulative decisions:\n• Treasury: $${(treasury / 1_000_000).toFixed(1)}M\n• Reputation: ${reputation}/100\n• Total CO₂: ${(globalState?.tco2e_emissions || 0).toLocaleString()} tonnes\n\nCheck the KPI trends on the left panel for detailed round-over-round changes.`;
    }

    return `I can help you with:\n\n1. **📋 Crisis Analysis** — Understanding the current round's challenge\n2. **⚖️ Option Comparison** — Comparing strategic options A/B/C\n3. **💰 Capital Allocation** — How to distribute your CSF Pool\n4. **🌱 ESG Improvement** — Strategies to boost sustainability scores\n5. **📊 Performance Review** — What happened in previous rounds\n\nTry asking one of these questions!`;
  };

  const handleSend = async (text) => {
    const query = text || input;
    if (!query.trim()) return;

    setMessages(prev => [...prev, { role: 'user', content: query }]);
    setInput('');
    setLoading(true);

    // Simulate AI thinking delay
    await new Promise(r => setTimeout(r, 600 + Math.random() * 800));
    const response = generateResponse(query);
    setMessages(prev => [...prev, { role: 'assistant', content: response }]);
    setLoading(false);
  };

  if (!isOpen) return null;

  return (
    <div style={{
      position: 'fixed', right: 16, bottom: 40, width: 380, maxHeight: '70vh',
      background: '#fff', borderRadius: 16, zIndex: 11000,
      boxShadow: '0 20px 60px rgba(0,0,0,0.2)', border: '1px solid #e2e8f0',
      display: 'flex', flexDirection: 'column', fontFamily: 'Inter, sans-serif',
      animation: 'fadeSlideUp 0.25s ease-out',
    }}>
      {/* Header */}
      <div style={{
        padding: '0.7rem 1rem', borderBottom: '1px solid #e2e8f0',
        display: 'flex', alignItems: 'center', justifyContent: 'space-between',
        background: 'linear-gradient(135deg, #6366f1, #8b5cf6)', borderRadius: '16px 16px 0 0',
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
          <span style={{ fontSize: '1.2rem' }}>🤖</span>
          <div>
            <div style={{ fontSize: '0.78rem', fontWeight: 700, color: '#fff' }}>Strategic Advisor</div>
            <div style={{ fontSize: '0.6rem', color: 'rgba(255,255,255,0.7)' }}>AI-powered assistant</div>
          </div>
        </div>
        <button onClick={onClose} style={{
          background: 'rgba(255,255,255,0.2)', border: 'none', borderRadius: '50%',
          width: 24, height: 24, cursor: 'pointer', color: '#fff', fontWeight: 700,
          fontSize: '0.75rem', display: 'flex', alignItems: 'center', justifyContent: 'center',
        }}>✕</button>
      </div>

      {/* Messages */}
      <div ref={scrollRef} style={{
        flex: 1, overflow: 'auto', padding: '0.6rem 0.8rem',
        display: 'flex', flexDirection: 'column', gap: 8, minHeight: 200, maxHeight: 350,
      }}>
        {messages.map((msg, i) => (
          <div key={i} style={{
            alignSelf: msg.role === 'user' ? 'flex-end' : 'flex-start',
            maxWidth: '85%',
            padding: '8px 12px', borderRadius: 12,
            background: msg.role === 'user'
              ? 'linear-gradient(135deg, #6366f1, #8b5cf6)'
              : '#f8fafc',
            color: msg.role === 'user' ? '#fff' : '#334155',
            fontSize: '0.73rem', lineHeight: 1.6,
            border: msg.role === 'assistant' ? '1px solid #e2e8f0' : 'none',
            whiteSpace: 'pre-wrap',
          }}>
            {msg.content}
          </div>
        ))}
        {loading && (
          <div style={{
            alignSelf: 'flex-start', padding: '8px 16px',
            background: '#f8fafc', borderRadius: 12, border: '1px solid #e2e8f0',
            fontSize: '0.73rem', color: '#94a3b8',
          }}>
            <span style={{ animation: 'pulse 1s infinite' }}>●</span> Thinking...
          </div>
        )}
      </div>

      {/* Preset prompts */}
      {messages.length <= 1 && (
        <div style={{
          padding: '0 0.8rem 0.4rem', display: 'flex', flexWrap: 'wrap', gap: 4,
        }}>
          {PRESET_PROMPTS.map(prompt => (
            <button
              key={prompt}
              onClick={() => handleSend(prompt)}
              style={{
                padding: '4px 8px', borderRadius: 6, border: '1px solid #e2e8f0',
                background: '#f8fafc', fontSize: '0.6rem', color: '#475569',
                cursor: 'pointer', fontFamily: 'Inter, sans-serif', fontWeight: 600,
              }}
            >{prompt}</button>
          ))}
        </div>
      )}

      {/* Input */}
      <div style={{
        padding: '0.5rem 0.8rem', borderTop: '1px solid #e2e8f0',
        display: 'flex', gap: 6,
      }}>
        <input
          type="text"
          value={input}
          onChange={e => setInput(e.target.value)}
          onKeyDown={e => e.key === 'Enter' && handleSend()}
          placeholder="Ask your advisor..."
          style={{
            flex: 1, padding: '7px 10px', borderRadius: 8,
            border: '1px solid #e2e8f0', fontSize: '0.75rem',
            outline: 'none', fontFamily: 'Inter, sans-serif',
          }}
        />
        <button
          onClick={() => handleSend()}
          disabled={!input.trim() || loading}
          style={{
            padding: '7px 14px', borderRadius: 8, border: 'none',
            background: '#6366f1', color: '#fff', fontWeight: 700,
            cursor: 'pointer', fontSize: '0.72rem',
            opacity: !input.trim() || loading ? 0.5 : 1,
          }}
        >Send</button>
      </div>
    </div>
  );
}
