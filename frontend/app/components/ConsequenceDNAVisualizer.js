'use client';
import React, { useState, useEffect, useMemo, useCallback, useRef } from 'react';
import styles from './ConsequenceDNAVisualizer.module.css';

/**
 * ConsequenceDNAVisualizer — Sankey Diagram Pop-Out
 *
 * Renders a 4-column Sankey diagram mapping:
 *   Col 1: Decision Nodes (R1–R10)
 *   Col 2: Causal Flag Nodes + Conflict Nodes (agent constriction)
 *   Col 3: Metric Shift Nodes
 *   Col 4: R10 M_R Projection Nodes
 *
 * Props:
 *   - sessionId:  current session ID (for API fetch)
 *   - isOpen:     boolean controlling visibility
 *   - onClose:    callback to close the pop-out
 *   - frozen:     if true, renders read-only snapshot mode (R10 report)
 *   - inline:     if true, renders without the full-screen overlay (for embedding)
 *   - snapshotData: pre-computed data for frozen mode (bypasses API)
 */

const API_BASE = process.env.NEXT_PUBLIC_API_URL || '';

// Layout constants
const SVG_W = 1400;
const SVG_H = 600;
const COL_X = [60, 380, 700, 900, 1200]; // decisions, flags, conflicts, metrics, projections
const NODE_W = 140;
const NODE_H = 36;
const CONFLICT_W = 120;
const CONFLICT_H = 44;
const COL_LABELS = ['DECISIONS', 'CAUSAL FLAGS', 'AGENTS', 'METRIC SHIFTS', 'M_R PROJECTIONS'];

// Color interpolation: Amber (LP12) → Emerald (LP1)
function leverageColor(level) {
  const t = Math.max(0, Math.min(1, (12 - level) / 11));
  const h = 38 + (152 - 38) * t;
  const s = 80 + 12 * t;
  const l = 50 - 5 * t;
  return `hsl(${h}, ${s}%, ${l}%)`;
}

function pathWidth(impactScore, maxImpact) {
  return 2 + (impactScore / Math.max(maxImpact, 1)) * 16;
}

// Cubic bezier path between two points
function bezierPath(x1, y1, x2, y2) {
  const cx = (x1 + x2) / 2;
  return `M${x1},${y1} C${cx},${y1} ${cx},${y2} ${x2},${y2}`;
}

// ── Trigger Button (shown in cockpit) ──
export function ConsequenceDNATrigger({ ignited, onClick }) {
  return (
    <button
      className={`${styles.triggerBtn} ${!ignited ? styles.triggerBtnDormant : ''}`}
      onClick={onClick}
      title="Open Consequence DNA Visualizer"
    >
      {ignited && <span className={styles.triggerPulse} />}
      <span>🧬</span>
      <span>{ignited ? 'Consequence DNA' : 'DNA Locked'}</span>
    </button>
  );
}


export default function ConsequenceDNAVisualizer({
  sessionId,
  isOpen,
  onClose,
  frozen = false,
  inline = false,
  snapshotData = null,
}) {
  const [data, setData] = useState(snapshotData || null);
  const [loading, setLoading] = useState(false);
  const [hoveredChain, setHoveredChain] = useState(null);
  const [hoveredLink, setHoveredLink] = useState(null); // {x, y, label} for path tooltip
  const svgRef = useRef(null);

  // Fetch data from API (or use snapshot)
  useEffect(() => {
    if (!isOpen || frozen) return;
    if (!sessionId || sessionId === 'demo') return;
    let cancelled = false;
    setLoading(true);
    fetch(`${API_BASE}/api/simulations/${sessionId}/consequence-dna-data`)
      .then(r => r.ok ? r.json() : null)
      .then(d => { if (!cancelled && d) setData(d); })
      .catch(() => {})
      .finally(() => { if (!cancelled) setLoading(false); });
    return () => { cancelled = true; };
  }, [isOpen, sessionId, frozen]);

  useEffect(() => {
    if (snapshotData) setData(snapshotData);
  }, [snapshotData]);

  // Close on Escape
  useEffect(() => {
    if (!isOpen) return;
    const handler = (e) => { if (e.key === 'Escape') onClose?.(); };
    window.addEventListener('keydown', handler);
    return () => window.removeEventListener('keydown', handler);
  }, [isOpen, onClose]);

  // ── Node layout computation ──
  const layout = useMemo(() => {
    if (!data) return null;
    const nodes = data.sankey_nodes || {};
    const decisions = nodes.decisions || [];
    const flags = nodes.flags || [];
    const conflicts = nodes.conflict_nodes || [];
    const metrics = nodes.metrics || [];
    const projections = nodes.projections || [];

    const positionColumn = (items, colIdx, h = NODE_H) => {
      const count = items.length || 1;
      const totalH = count * h + (count - 1) * 10;
      const startY = Math.max(40, (SVG_H - totalH) / 2);
      return items.map((item, i) => ({
        ...item,
        x: COL_X[colIdx],
        y: startY + i * (h + 10),
        w: colIdx === 2 ? CONFLICT_W : NODE_W,
        h,
      }));
    };

    return {
      decisions: positionColumn(decisions, 0),
      flags: positionColumn(flags, 1),
      conflicts: positionColumn(conflicts, 2, CONFLICT_H),
      metrics: positionColumn(metrics, 3),
      projections: positionColumn(projections, 4),
    };
  }, [data]);

  // ── Precomputed node lookup map for O(1) access (performance memoization) ──
  const nodeMap = useMemo(() => {
    if (!layout) return {};
    const map = {};
    for (const col of Object.values(layout)) {
      for (const node of col) {
        if (node.id) map[node.id] = node;
        if (node.agent_id) map[node.agent_id] = node;
      }
    }
    return map;
  }, [layout]);

  // ── Build a lookup for hover chain highlighting ──
  const chainMap = useMemo(() => {
    if (!data) return {};
    const map = {};
    for (const link of (data.sankey_links || [])) {
      if (!map[link.source]) map[link.source] = new Set();
      if (!map[link.target]) map[link.target] = new Set();
      map[link.source].add(link.target);
      map[link.target].add(link.source);
    }
    return map;
  }, [data]);

  const getChainIds = useCallback((nodeId) => {
    if (!chainMap[nodeId]) return new Set();
    const visited = new Set([nodeId]);
    const queue = [nodeId];
    while (queue.length) {
      const current = queue.shift();
      for (const neighbor of (chainMap[current] || [])) {
        if (!visited.has(neighbor)) {
          visited.add(neighbor);
          queue.push(neighbor);
        }
      }
    }
    return visited;
  }, [chainMap]);

  const handleHover = useCallback((nodeId) => {
    setHoveredChain(nodeId ? getChainIds(nodeId) : null);
  }, [getChainIds]);

  // ── PNG Export ──
  const handleCapture = useCallback(() => {
    const svg = svgRef.current;
    if (!svg) return;
    const serializer = new XMLSerializer();
    const svgStr = serializer.serializeToString(svg);
    const canvas = document.createElement('canvas');
    canvas.width = SVG_W * 2;
    canvas.height = SVG_H * 2;
    const ctx = canvas.getContext('2d');
    const img = new Image();
    const blob = new Blob([svgStr], { type: 'image/svg+xml;charset=utf-8' });
    const url = URL.createObjectURL(blob);
    img.onload = () => {
      ctx.fillStyle = '#0f172a';
      ctx.fillRect(0, 0, canvas.width, canvas.height);
      ctx.drawImage(img, 0, 0, canvas.width, canvas.height);
      URL.revokeObjectURL(url);
      const link = document.createElement('a');
      link.download = `consequence-dna-${sessionId || 'snapshot'}.png`;
      link.href = canvas.toDataURL('image/png');
      link.click();
    };
    img.src = url;
  }, [sessionId]);

  if (!isOpen) return null;

  const ignited = data?.ignited ?? false;
  const mr = data?.mr_projection || {};
  const leverageSummary = data?.leverage_summary || {};
  const maxImpact = Math.max(...(data?.sankey_nodes?.decisions || []).map(d => d.impact_score || 1), 1);

  // Node check helper for dimming
  const isNodeHighlighted = (id) => !hoveredChain || hoveredChain.has(id);

  // Inline mode: render panel directly without overlay wrapper
  const panelContent = (
    <div className={`${styles.panel} ${ignited ? styles.panelIgnited : ''} ${frozen ? styles.frozen : ''} ${inline ? styles.panelInline : ''}`}>
        {/* Header */}
        <div className={styles.header}>
          <div className={styles.headerLeft}>
            <span className={styles.dnaIcon}>🧬</span>
            <div>
              <div className={styles.title}>CONSEQUENCE DNA VISUALIZER</div>
              <div className={styles.subtitle}>
                {frozen ? 'System Freeze — Final State Captured' : 'Decision-to-Outcome Dependency Map'}
              </div>
            </div>
          </div>
          <div className={styles.headerRight}>
            <div className={styles.legendBar}>
              <span>Shallow (LP12)</span>
              <div className={styles.legendGradient} />
              <span>Deep (LP1)</span>
            </div>
            <button className={styles.captureBtn} onClick={handleCapture}>📸 Export PNG</button>
            <button className={styles.closeBtn} onClick={onClose}>✕ Close</button>
          </div>
        </div>

        {frozen && <div className={styles.frozenBadge}>🔒 SYSTEM FREEZE — R10</div>}

        {/* SVG Canvas */}
        <div className={styles.sankeyContainer}>
          {!ignited && !frozen && (
            <div className={styles.dormantOverlay}>
              <div className={styles.dormantIcon}>🔒</div>
              <div className={styles.dormantText}>
                The Consequence DNA Visualizer activates after the Round 5 Shadow Board Audit.
              </div>
              {data?.current_round >= 4 && (
                <div className={styles.teaserText}>
                  ⚡ {(data?.sankey_nodes?.decisions || []).length} causal chains detected — awaiting ignition
                </div>
              )}
            </div>
          )}

          {(ignited || frozen) && layout && (
            <svg
              ref={svgRef}
              className={styles.sankeySvg}
              viewBox={`0 0 ${SVG_W} ${SVG_H}`}
              preserveAspectRatio="xMidYMid meet"
            >
              {/* Column headers */}
              {COL_LABELS.map((label, i) => (
                <text key={label} x={COL_X[i] + (i === 2 ? CONFLICT_W / 2 : NODE_W / 2)} y={22} textAnchor="middle" className={styles.colHeader}>
                  {label}
                </text>
              ))}

              {/* ── Sankey Paths ── */}
              {(data.sankey_links || []).map((link, i) => {
                const sourceNode = nodeMap[link.source];
                const targetNode = nodeMap[link.target];
                if (!sourceNode || !targetNode) return null;
                const x1 = sourceNode.x + sourceNode.w;
                const y1 = sourceNode.y + sourceNode.h / 2;
                const x2 = targetNode.x;
                const y2 = targetNode.y + targetNode.h / 2;
                const cx = (x1 + x2) / 2;
                const cy = (y1 + y2) / 2;
                const width = pathWidth(link.value || 1, maxImpact);
                const color = leverageColor(link.leverage_level || 12);
                const highlighted = isNodeHighlighted(link.source) && isNodeHighlighted(link.target);

                return (
                  <path
                    key={`link-${i}`}
                    d={bezierPath(x1, y1, x2, y2)}
                    className={`${styles.sankeyPath} ${!highlighted ? styles.sankeyPathDimmed : ''} ${highlighted && hoveredChain ? styles.sankeyPathHighlighted : ''} ${!frozen ? styles.pathDrawIn : ''}`}
                    style={{
                      stroke: link.active ? color : 'rgba(148, 163, 184, 0.2)',
                      strokeWidth: width,
                      animationDelay: `${i * 0.15}s`,
                      cursor: 'pointer',
                    }}
                    onMouseEnter={() => setHoveredLink({
                      x: cx, y: cy - 14,
                      label: `LP${link.leverage_level || '?'} · Impact: ${(link.value || 0).toFixed(1)}`,
                      color: link.active ? color : '#94a3b8',
                    })}
                    onMouseLeave={() => setHoveredLink(null)}
                  />
                );
              })}

              {/* ── Path Tooltip ── */}
              {hoveredLink && (
                <g className={styles.pathTooltip}>
                  <rect
                    x={hoveredLink.x - 60} y={hoveredLink.y - 10}
                    width={120} height={20} rx={5}
                    fill="rgba(15,23,42,0.92)" stroke={hoveredLink.color} strokeWidth={1}
                  />
                  <text
                    x={hoveredLink.x} y={hoveredLink.y + 3}
                    textAnchor="middle" fontSize="9" fontWeight="700"
                    fill={hoveredLink.color} fontFamily="var(--font-mono, monospace)"
                  >
                    {hoveredLink.label}
                  </text>
                </g>
              )}

              {/* ── Leak Paths (triggered agents) ── */}
              {(layout.conflicts || []).filter(c => c.leak_active).map((conflict, i) => {
                const leakX = conflict.x + conflict.w;
                const leakY = conflict.y + conflict.h / 2;
                return (
                  <g key={`leak-${i}`}>
                    <path
                      d={`M${leakX},${leakY} Q${leakX + 60},${leakY + 30} ${leakX + 100},${leakY + 50}`}
                      className={styles.leakPath}
                      strokeWidth={3}
                    />
                    <text x={leakX + 105} y={leakY + 55} fontSize="8" fill="#ef4444" fontWeight="700">
                      {conflict.leak_label}
                    </text>
                  </g>
                );
              })}

              {/* ── Interference Pair Arrows ── */}
              {(data.interference_pairs || []).map((pair, i) => {
                const a = (layout.conflicts || []).find(c => c.agent_id === pair.agent_a);
                const b = (layout.conflicts || []).find(c => c.agent_id === pair.agent_b);
                if (!a || !b) return null;
                return (
                  <line
                    key={`interf-${i}`}
                    x1={a.x + a.w / 2} y1={a.y + a.h}
                    x2={b.x + b.w / 2} y2={b.y}
                    className={styles.interferenceLine}
                  />
                );
              })}

              {/* ── Cascade Pulses ── */}
              {(data.cascade_events || []).map((cascade, i) => {
                const sourceConflict = (layout.conflicts || []).find(c => c.agent_id === cascade.source);
                const targetConflict = (layout.conflicts || []).find(c => c.agent_id === cascade.target);
                if (!sourceConflict || !targetConflict) return null;
                const pathId = `cascade-path-${i}`;
                return (
                  <g key={`cascade-${i}`}>
                    <path
                      id={pathId}
                      d={bezierPath(
                        sourceConflict.x + sourceConflict.w / 2, sourceConflict.y + sourceConflict.h,
                        targetConflict.x + targetConflict.w / 2, targetConflict.y
                      )}
                      fill="none" stroke="none"
                    />
                    <circle r="4" className={styles.cascadePulse}>
                      <animateMotion dur="0.8s" repeatCount="3" begin="0s">
                        <mpath href={`#${pathId}`} />
                      </animateMotion>
                    </circle>
                  </g>
                );
              })}

              {/* ── Decision Nodes (Col 1) ── */}
              {(layout.decisions || []).map((node) => (
                <g
                  key={node.id}
                  className={`${styles.nodeGroup} ${!isNodeHighlighted(node.id) ? styles.nodeGroupDimmed : ''}`}
                  onMouseEnter={() => handleHover(node.id)}
                  onMouseLeave={() => handleHover(null)}
                >
                  <rect
                    x={node.x} y={node.y} width={node.w} height={node.h}
                    className={styles.nodeRect}
                    fill={leverageColor(node.leverage_level || 12)}
                    fillOpacity={0.2}
                    stroke={leverageColor(node.leverage_level || 12)}
                  />
                  <text x={node.x + 8} y={node.y + 15} className={styles.nodeLabel}>
                    {truncate(node.label, 22)}
                  </text>
                  <text x={node.x + 8} y={node.y + 27} className={styles.nodeSublabel}>
                    LP{node.leverage_level} · Impact: {(node.impact_score || 0).toFixed(1)}
                  </text>
                </g>
              ))}

              {/* ── Flag Nodes (Col 2) ── */}
              {(layout.flags || []).map((node) => (
                <g
                  key={node.id}
                  className={`${styles.nodeGroup} ${!isNodeHighlighted(node.id) ? styles.nodeGroupDimmed : ''}`}
                  onMouseEnter={() => handleHover(node.id)}
                  onMouseLeave={() => handleHover(null)}
                >
                  <rect
                    x={node.x} y={node.y} width={node.w} height={node.h}
                    className={styles.nodeRect}
                    fill={node.active ? 'rgba(16, 185, 129, 0.12)' : 'rgba(148, 163, 184, 0.06)'}
                    stroke={node.active ? '#10b981' : 'rgba(148, 163, 184, 0.2)'}
                  />
                  <text x={node.x + 8} y={node.y + 15} className={styles.nodeLabel}>
                    {truncate(node.label, 22)}
                  </text>
                  <text x={node.x + 8} y={node.y + 27} className={styles.nodeSublabel}>
                    R{node.source_round}→R{node.target_round} · {node.category}
                  </text>
                </g>
              ))}

              {/* ── Conflict Nodes (Col 2.5) ── */}
              {(layout.conflicts || []).map((node) => {
                const constriction = node.constriction_factor || 0;
                const stageColor = {
                  dormant: 'rgba(148, 163, 184, 0.15)',
                  watching: 'rgba(245, 158, 11, 0.15)',
                  agitated: 'rgba(245, 158, 11, 0.3)',
                  hostile: 'rgba(239, 68, 68, 0.25)',
                  triggered: 'rgba(239, 68, 68, 0.4)',
                }[node.stage] || 'rgba(148, 163, 184, 0.1)';
                const borderColor = {
                  dormant: 'rgba(148, 163, 184, 0.2)',
                  watching: 'rgba(245, 158, 11, 0.4)',
                  agitated: 'rgba(245, 158, 11, 0.6)',
                  hostile: 'rgba(239, 68, 68, 0.5)',
                  triggered: '#ef4444',
                }[node.stage] || 'rgba(148, 163, 184, 0.2)';

                return (
                  <g
                    key={node.agent_id}
                    className={`${styles.conflictNode} ${node.stage === 'triggered' ? styles.cascadeFlash : ''}`}
                  >
                    <rect
                      x={node.x} y={node.y} width={node.w} height={node.h}
                      className={styles.conflictRect}
                      fill={stageColor}
                      stroke={borderColor}
                    />
                    {/* Constriction bar */}
                    {constriction > 0 && (
                      <rect
                        x={node.x} y={node.y + node.h - 4}
                        width={node.w * constriction} height={4}
                        fill="rgba(239, 68, 68, 0.6)" rx={2}
                      />
                    )}
                    <text x={node.x + 6} y={node.y + 14} className={styles.conflictLabel}>
                      {node.icon} {truncate(node.name, 16)}
                    </text>
                    <text x={node.x + 6} y={node.y + 26} className={styles.conflictStage}>
                      {node.stage} · CF: {(constriction * 100).toFixed(0)}%
                    </text>
                    <text x={node.x + 6} y={node.y + 37} className={styles.nodeSublabel}>
                      {node.flow_source} → {node.flow_target}
                    </text>
                  </g>
                );
              })}

              {/* ── Metric Nodes (Col 3) ── */}
              {(layout.metrics || []).map((node) => (
                <g
                  key={node.id}
                  className={`${styles.nodeGroup} ${!isNodeHighlighted(node.id) ? styles.nodeGroupDimmed : ''}`}
                  onMouseEnter={() => handleHover(node.id)}
                  onMouseLeave={() => handleHover(null)}
                >
                  <rect
                    x={node.x} y={node.y} width={node.w} height={node.h}
                    className={styles.nodeRect}
                    fill={node.delta > 0 ? 'rgba(16, 185, 129, 0.12)' : 'rgba(239, 68, 68, 0.12)'}
                    stroke={node.delta > 0 ? '#10b981' : '#ef4444'}
                  />
                  <text x={node.x + 8} y={node.y + 15} className={styles.nodeLabel}>
                    {truncate(node.label, 22)}
                  </text>
                  <text x={node.x + 8} y={node.y + 27} className={styles.nodeSublabel}>
                    {node.delta > 0 ? '+' : ''}{node.delta} {node.metric}
                  </text>
                </g>
              ))}

              {/* ── Projection Nodes (Col 4) ── */}
              {(layout.projections || []).map((node) => (
                <g
                  key={node.id}
                  className={`${styles.nodeGroup} ${!isNodeHighlighted(node.id) ? styles.nodeGroupDimmed : ''}`}
                  onMouseEnter={() => handleHover(node.id)}
                  onMouseLeave={() => handleHover(null)}
                >
                  <rect
                    x={node.x} y={node.y} width={node.w} height={node.h}
                    className={styles.nodeRect}
                    fill={node.mr_delta > 0 ? 'rgba(16, 185, 129, 0.15)' : 'rgba(239, 68, 68, 0.15)'}
                    stroke={node.mr_delta > 0 ? '#10b981' : '#ef4444'}
                  />
                  <text x={node.x + 8} y={node.y + 15} className={styles.nodeLabel}>
                    {truncate(node.label, 22)}
                  </text>
                  <text x={node.x + 8} y={node.y + 27} className={styles.nodeSublabel}>
                    M_R {node.mr_delta > 0 ? '+' : ''}{node.mr_delta?.toFixed(2)}
                  </text>
                </g>
              ))}

              {/* ── Senge Archetype Badges ── */}
              {(data.archetype_badges || []).map((badge, i) => (
                <g key={`badge-${i}`} className={styles.badge}>
                  <rect
                    x={COL_X[1] + NODE_W + 5}
                    y={35 + i * 18}
                    width={badge.name.length * 5 + 20}
                    height={14}
                    className={styles.badgeRect}
                  />
                  <text
                    x={COL_X[1] + NODE_W + 15}
                    y={35 + i * 18 + 10}
                    className={styles.badgeText}
                  >
                    ⚠ {badge.name}
                  </text>
                </g>
              ))}
            </svg>
          )}

          {loading && !data && (
            <div className={styles.dormantOverlay}>
              <div className={styles.dormantIcon}>⏳</div>
              <div className={styles.dormantText}>Loading Consequence DNA data…</div>
            </div>
          )}
        </div>

        {/* Footer Stats */}
        <div className={styles.footer}>
          <div className={styles.statGroup}>
            <div className={styles.stat}>
              <span className={styles.statValue}>{leverageSummary.deep_intervention_count || 0}</span>
              <span className={styles.statLabel}>Deep Interventions</span>
            </div>
            <div className={styles.stat}>
              <span className={styles.statValue}>{leverageSummary.shallow_intervention_count || 0}</span>
              <span className={styles.statLabel}>Shallow Interventions</span>
            </div>
            <div className={styles.stat}>
              <span className={styles.statValue}>{((leverageSummary.effectiveness_score || 0) * 100).toFixed(0)}%</span>
              <span className={styles.statLabel}>System Effectiveness</span>
            </div>
            <div className={styles.stat}>
              <span className={styles.statValue}>
                {(data?.agents || []).filter(a => ['agitated', 'hostile', 'triggered'].includes(a.stage)).length}
              </span>
              <span className={styles.statLabel}>Active Conflicts</span>
            </div>
          </div>
          <div className={styles.mrProjection}>
            <div>
              <span className={styles.mrValue} style={{
                color: mr.mr >= 1.8 ? '#10b981' : mr.mr >= 1.2 ? '#3b82f6' : mr.mr >= 0.8 ? '#f59e0b' : '#ef4444',
              }}>
                {(mr.mr || 1.0).toFixed(2)}
              </span>
              <span className={styles.mrLabel}> M_R</span>
            </div>
            {mr.archetype && (
              <span
                className={styles.archetypeBadge}
                style={{ background: mr.archetype.gradient, color: '#fff' }}
              >
                {mr.archetype.icon} {mr.archetype.title}
              </span>
            )}
          </div>
      </div>
    </div>
  );

  // Inline mode: no overlay wrapper
  if (inline) return panelContent;

  // Pop-out mode: full overlay
  return (
    <div className={styles.overlay} onClick={(e) => { if (e.target === e.currentTarget) onClose?.(); }}>
      {panelContent}
    </div>
  );
}


// ── Helpers ──

function truncate(str, max) {
  if (!str) return '';
  return str.length > max ? str.slice(0, max - 1) + '…' : str;
}

function findNode(layout, id) {
  if (!layout) return null;
  for (const col of Object.values(layout)) {
    const found = col.find(n => n.id === id || n.agent_id === id);
    if (found) return found;
  }
  return null;
}
