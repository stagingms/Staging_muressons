'use client';
import React, { useState, useMemo, useCallback, useRef, useEffect, Suspense } from 'react';
import { Canvas, useFrame, useThree } from '@react-three/fiber';
import { OrbitControls, Html, Float, Line } from '@react-three/drei';
import * as THREE from 'three';
import styles from './ESGImpactConstellation.module.css';
import { currencySymbol, atRate } from '../utils/format';

// ══════════════════════════════════════════════════════════════
//  ESG DIMENSION COLORS — from globals.css token system
// ══════════════════════════════════════════════════════════════
const ESG_COLORS = {
  environmental: '#10b981',
  social: '#3b82f6',
  governance: '#8b5cf6',
  financial: '#f59e0b',
  mixed: '#5eead4',
};

const ROUND_LABELS = {
  1: 'ESG Materiality',
  2: 'Double Materiality',
  3: 'Scope 3 Supply Chain',
  4: 'ESG Contagion',
  5: 'Climate Risk',
  6: 'AI Ethics',
  7: 'Circular Economy',
  8: 'Water Stress',
  9: 'Just Transition',
  10: 'Activist Ultimatum',
};

// ══════════════════════════════════════════════════════════════
//  DATA TRANSFORMER — Converts simulation history to graph data
// ══════════════════════════════════════════════════════════════
function buildConstellationData(history, currentRound) {
  const nodes = [];
  const edges = [];

  if (!history || history.length === 0) return { nodes, edges };

  history.forEach((round, idx) => {
    const r = round.round_number || idx + 1;
    const gs = round.global_state || {};
    const decisions = gs.active_event_flags?.round_decisions || {};

    // Determine ESG dimension from round content
    let dimension = 'mixed';
    if ([1, 3, 5, 7, 8].includes(r)) dimension = 'environmental';
    else if ([4, 9].includes(r)) dimension = 'social';
    else if ([2, 6].includes(r)) dimension = 'governance';

    // Calculate impact magnitude from treasury change
    const prevTreasury = idx > 0 ? (history[idx - 1].global_state?.corporate_treasury || 0) : 0;
    const currTreasury = gs.corporate_treasury || 0;
    const treasuryDelta = currTreasury - prevTreasury;
    const magnitude = Math.abs(treasuryDelta);

    // Calculate reputation change
    const prevRep = idx > 0 ? (history[idx - 1].global_state?.group_reputation || 50) : 50;
    const currRep = gs.group_reputation || 50;
    const repDelta = currRep - prevRep;

    // Calculate carbon change
    const prevCarbon = idx > 0 ? (history[idx - 1].global_state?.tco2e_emissions || 0) : 0;
    const currCarbon = gs.tco2e_emissions || 0;
    const carbonDelta = currCarbon - prevCarbon;

    // Position in 3D space — spiral layout
    const angle = (r / 10) * Math.PI * 2.5;
    const radius = 2 + r * 0.6;
    const x = Math.cos(angle) * radius;
    const z = Math.sin(angle) * radius;
    const y = (r - 5.5) * 0.8; // vertical spread

    nodes.push({
      id: `r${r}`,
      round: r,
      label: ROUND_LABELS[r] || `Round ${r}`,
      dimension,
      color: ESG_COLORS[dimension],
      position: [x, y, z],
      size: Math.max(0.15, Math.min(0.5, magnitude / 5_000_000)),
      treasuryDelta,
      repDelta,
      carbonDelta,
      treasury: currTreasury,
      reputation: currRep,
      carbon: currCarbon,
      decisions: typeof decisions === 'object' ? JSON.stringify(decisions) : decisions,
    });

    // Causal edges: each round connects to the next
    if (idx > 0) {
      edges.push({
        from: `r${history[idx - 1].round_number || idx}`,
        to: `r${r}`,
        strength: Math.abs(repDelta) / 20, // 0-1 scale
      });
    }

    // Cross-links for systemic effects
    if (r === 5 && history.find(h => h.round_number === 3)) {
      edges.push({ from: 'r3', to: 'r5', strength: 0.6, type: 'causal' });
    }
    if (r === 7 && history.find(h => h.round_number === 4)) {
      edges.push({ from: 'r4', to: 'r7', strength: 0.4, type: 'causal' });
    }
    if (r === 10 && history.find(h => h.round_number === 1)) {
      edges.push({ from: 'r1', to: 'r10', strength: 0.8, type: 'causal' });
    }
  });

  return { nodes, edges };
}

// ══════════════════════════════════════════════════════════════
//  3D NODE — Glowing sphere for each decision round
// ══════════════════════════════════════════════════════════════
function DecisionNode({ node, isFiltered, isSelected, onSelect, onHover }) {
  const meshRef = useRef();
  const glowRef = useRef();
  const [hovered, setHovered] = useState(false);

  useFrame((state) => {
    if (meshRef.current) {
      // Gentle pulse
      const scale = node.size * (1 + Math.sin(state.clock.elapsedTime * 1.5 + node.round) * 0.08);
      meshRef.current.scale.setScalar(scale);

      // Rotation
      meshRef.current.rotation.y += 0.003;
    }
    if (glowRef.current) {
      glowRef.current.material.opacity = 0.15 + Math.sin(state.clock.elapsedTime * 2 + node.round) * 0.05;
    }
  });

  const handlePointerOver = useCallback((e) => {
    e.stopPropagation();
    setHovered(true);
    onHover(node);
    document.body.style.cursor = 'pointer';
  }, [node, onHover]);

  const handlePointerOut = useCallback(() => {
    setHovered(false);
    onHover(null);
    document.body.style.cursor = 'auto';
  }, [onHover]);

  const opacity = isFiltered ? 1 : 0.15;

  return (
    <group position={node.position}>
      {/* Glow sphere */}
      <mesh ref={glowRef}>
        <sphereGeometry args={[node.size * 2.5, 16, 16]} />
        <meshBasicMaterial
          color={node.color}
          transparent
          opacity={0.1 * opacity}
          side={THREE.BackSide}
        />
      </mesh>

      {/* Core sphere */}
      <mesh
        ref={meshRef}
        onPointerOver={handlePointerOver}
        onPointerOut={handlePointerOut}
        onClick={(e) => { e.stopPropagation(); onSelect(node); }}
      >
        <sphereGeometry args={[1, 24, 24]} />
        <meshStandardMaterial
          color={node.color}
          emissive={node.color}
          emissiveIntensity={hovered || isSelected ? 0.8 : 0.3}
          roughness={0.3}
          metalness={0.6}
          transparent
          opacity={opacity}
        />
      </mesh>

      {/* Round label */}
      {(hovered || isSelected) && (
        <Html center distanceFactor={8} style={{ pointerEvents: 'none' }}>
          <div style={{
            background: 'rgba(15,23,42,0.9)',
            border: `1px solid ${node.color}40`,
            borderRadius: 6,
            padding: '3px 8px',
            whiteSpace: 'nowrap',
            fontSize: 'var(--type-caption)',
            fontWeight: 700,
            color: node.color,
            fontFamily: "'DM Sans', sans-serif",
          }}>
            R{node.round}: {node.label}
          </div>
        </Html>
      )}
    </group>
  );
}

// ══════════════════════════════════════════════════════════════
//  3D EDGE — Animated particle stream between nodes
// ══════════════════════════════════════════════════════════════
function CausalEdge({ from, to, strength = 0.5, type, isFiltered }) {
  const lineRef = useRef();
  const opacity = isFiltered ? 0.3 + strength * 0.4 : 0.05;
  const color = type === 'causal' ? '#f59e0b' : '#5eead4';

  // Create curve between points
  const points = useMemo(() => {
    const start = new THREE.Vector3(...from);
    const end = new THREE.Vector3(...to);
    const mid = start.clone().add(end).multiplyScalar(0.5);
    mid.y += 0.5 + strength;

    const curve = new THREE.QuadraticBezierCurve3(start, mid, end);
    return curve.getPoints(20);
  }, [from, to, strength]);

  return (
    <Line
      points={points}
      color={color}
      lineWidth={1 + strength * 2}
      transparent
      opacity={opacity}
      dashed={type === 'causal'}
      dashSize={0.3}
      dashScale={2}
    />
  );
}

// ══════════════════════════════════════════════════════════════
//  AMBIENT NEBULA — Background that shifts with game state
// ══════════════════════════════════════════════════════════════
function AmbientNebula({ reputation }) {
  const meshRef = useRef();

  // Reputation → color: green (thriving) → red (stressed)
  const color = useMemo(() => {
    if (reputation >= 65) return '#10b981';
    if (reputation >= 40) return '#f59e0b';
    return '#ef4444';
  }, [reputation]);

  useFrame((state) => {
    if (meshRef.current) {
      meshRef.current.rotation.x = state.clock.elapsedTime * 0.02;
      meshRef.current.rotation.y = state.clock.elapsedTime * 0.015;
    }
  });

  return (
    <mesh ref={meshRef} position={[0, 0, 0]}>
      <sphereGeometry args={[20, 32, 32]} />
      <meshBasicMaterial
        color={color}
        transparent
        opacity={0.03}
        side={THREE.BackSide}
      />
    </mesh>
  );
}

// ══════════════════════════════════════════════════════════════
//  PARTICLE FIELD — Ambient floating particles
// ══════════════════════════════════════════════════════════════
function ParticleField() {
  const particlesRef = useRef();
  const count = 200;

  const positions = useMemo(() => {
    const pos = new Float32Array(count * 3);
    for (let i = 0; i < count; i++) {
      pos[i * 3] = (Math.random() - 0.5) * 30;
      pos[i * 3 + 1] = (Math.random() - 0.5) * 20;
      pos[i * 3 + 2] = (Math.random() - 0.5) * 30;
    }
    return pos;
  }, []);

  useFrame((state) => {
    if (particlesRef.current) {
      particlesRef.current.rotation.y = state.clock.elapsedTime * 0.01;
    }
  });

  return (
    <points ref={particlesRef}>
      <bufferGeometry>
        <bufferAttribute
          attach="attributes-position"
          array={positions}
          count={count}
          itemSize={3}
        />
      </bufferGeometry>
      <pointsMaterial
        color="#5eead4"
        size={0.03}
        transparent
        opacity={0.3}
        sizeAttenuation
      />
    </points>
  );
}

// ══════════════════════════════════════════════════════════════
//  SCENE — Main 3D scene composition
// ══════════════════════════════════════════════════════════════
function ConstellationScene({ nodes, edges, filter, timelineMax, selectedNode, onSelectNode, onHoverNode }) {
  const filteredNodeIds = useMemo(() => {
    return new Set(
      nodes
        .filter(n => n.round <= timelineMax)
        .filter(n => filter === 'all' || n.dimension === filter)
        .map(n => n.id)
    );
  }, [nodes, filter, timelineMax]);

  const reputation = nodes.length > 0 ? nodes[nodes.length - 1].reputation : 50;

  return (
    <>
      <ambientLight intensity={0.3} />
      <pointLight position={[10, 10, 10]} intensity={0.5} color="#5eead4" />
      <pointLight position={[-10, -5, -10]} intensity={0.3} color="#818cf8" />

      <AmbientNebula reputation={reputation} />
      <ParticleField />

      {/* Render edges */}
      {edges.map((edge, i) => {
        const fromNode = nodes.find(n => n.id === edge.from);
        const toNode = nodes.find(n => n.id === edge.to);
        if (!fromNode || !toNode) return null;
        if (fromNode.round > timelineMax || toNode.round > timelineMax) return null;
        const isFiltered = filteredNodeIds.has(edge.from) && filteredNodeIds.has(edge.to);
        return (
          <CausalEdge
            key={`${edge.from}-${edge.to}-${i}`}
            from={fromNode.position}
            to={toNode.position}
            strength={edge.strength}
            type={edge.type}
            isFiltered={isFiltered}
          />
        );
      })}

      {/* Render nodes */}
      {nodes.filter(n => n.round <= timelineMax).map(node => (
        <Float
          key={node.id}
          speed={0.5}
          rotationIntensity={0}
          floatIntensity={0.3}
          floatingRange={[-0.05, 0.05]}
        >
          <DecisionNode
            node={node}
            isFiltered={filteredNodeIds.has(node.id)}
            isSelected={selectedNode?.id === node.id}
            onSelect={onSelectNode}
            onHover={onHoverNode}
          />
        </Float>
      ))}

      <OrbitControls
        enablePan
        enableZoom
        enableRotate
        autoRotate
        autoRotateSpeed={0.3}
        maxDistance={25}
        minDistance={4}
        dampingFactor={0.05}
        enableDamping
      />
    </>
  );
}

// ══════════════════════════════════════════════════════════════
//  MAIN COMPONENT
// ══════════════════════════════════════════════════════════════
export default function ESGImpactConstellation({ history, currentRound, onClose }) {
  const [filter, setFilter] = useState('all');
  const [timelineMax, setTimelineMax] = useState(currentRound || 10);
  const [selectedNode, setSelectedNode] = useState(null);
  const [hoveredNode, setHoveredNode] = useState(null);
  const [tooltipPos, setTooltipPos] = useState({ x: 0, y: 0 });

  const { nodes, edges } = useMemo(
    () => buildConstellationData(history, currentRound),
    [history, currentRound]
  );

  // Track mouse for tooltip
  useEffect(() => {
    const handler = (e) => setTooltipPos({ x: e.clientX, y: e.clientY });
    window.addEventListener('mousemove', handler);
    return () => window.removeEventListener('mousemove', handler);
  }, []);

  // ESC to close
  useEffect(() => {
    const handler = (e) => { if (e.key === 'Escape') onClose(); };
    window.addEventListener('keydown', handler);
    return () => window.removeEventListener('keydown', handler);
  }, [onClose]);

  const handleSelectNode = useCallback((node) => {
    setSelectedNode(prev => prev?.id === node.id ? null : node);
  }, []);

  const handleHoverNode = useCallback((node) => {
    setHoveredNode(node);
  }, []);

  const fmtK = (v) => {
    if (Math.abs(v) >= 1_000_000) return `${currencySymbol()}${atRate(v / 1_000_000).toFixed(1)}M`;
    if (Math.abs(v) >= 1_000) return `${currencySymbol()}${atRate(v / 1_000).toFixed(0)}K`;
    return `${currencySymbol()}${Math.round(atRate(v))}`;
  };

  const displayNode = hoveredNode || selectedNode;

  if (nodes.length === 0) {
    return (
      <div className={styles.overlay}>
        <div className={styles.header}>
          <div className={styles.headerLeft}>
            <span className={styles.title}>🌐 ESG Impact Constellation</span>
          </div>
          <button className={styles.closeBtn} onClick={onClose}>ESC · Close</button>
        </div>
        <div className={styles.canvasContainer}>
          <div className={styles.emptyState}>
            <span className={styles.emptyIcon}>🌌</span>
            <span className={styles.emptyText}>
              Complete at least one round to see your decision constellation take shape.
            </span>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className={styles.overlay}>
      {/* Header */}
      <div className={styles.header}>
        <div className={styles.headerLeft}>
          <span className={styles.title}>🌐 ESG Impact Constellation</span>
          <span className={styles.subtitle}>
            {nodes.length} decision nodes · {edges.length} causal links
          </span>
        </div>
        <button className={styles.closeBtn} onClick={onClose}>ESC · Close</button>
      </div>

      {/* 3D Canvas */}
      <div className={styles.canvasContainer}>
        <Canvas
          camera={{ position: [8, 4, 8], fov: 55, near: 0.1, far: 100 }}
          gl={{ antialias: true, alpha: true }}
          dpr={[1, 2]}
        >
          <Suspense fallback={null}>
            <ConstellationScene
              nodes={nodes}
              edges={edges}
              filter={filter}
              timelineMax={timelineMax}
              selectedNode={selectedNode}
              onSelectNode={handleSelectNode}
              onHoverNode={handleHoverNode}
            />
          </Suspense>
        </Canvas>

        {/* Legend */}
        <div className={styles.legend}>
          <span className={styles.legendTitle}>Dimensions</span>
          {Object.entries(ESG_COLORS).map(([key, color]) => (
            <span key={key} className={styles.legendItem}>
              <span className={styles.legendDot} style={{ background: color }} />
              {key.charAt(0).toUpperCase() + key.slice(1)}
            </span>
          ))}
        </div>

        {/* Stats Panel */}
        <div className={styles.statsPanel}>
          <div className={styles.statRow}>
            <span className={styles.statLabel}>Nodes</span>
            <span className={styles.statValue}>{nodes.filter(n => n.round <= timelineMax).length}</span>
          </div>
          <div className={styles.statRow}>
            <span className={styles.statLabel}>Links</span>
            <span className={styles.statValue}>{edges.length}</span>
          </div>
          <div className={styles.statRow}>
            <span className={styles.statLabel}>Viewing</span>
            <span className={styles.statValue}>R1–R{timelineMax}</span>
          </div>
        </div>

        {/* Tooltip */}
        {displayNode && (
          <div
            className={styles.tooltip}
            style={{
              left: Math.min(tooltipPos.x + 16, window.innerWidth - 300),
              top: Math.min(tooltipPos.y - 20, window.innerHeight - 200),
            }}
          >
            <div className={styles.tooltipRound}>Round {displayNode.round}</div>
            <div className={styles.tooltipTitle}>{displayNode.label}</div>
            <div className={styles.tooltipRow}>
              <span>Treasury Δ</span>
              <span className={`${styles.tooltipDelta} ${displayNode.treasuryDelta >= 0 ? styles.tooltipDeltaUp : styles.tooltipDeltaDown}`}>
                {displayNode.treasuryDelta >= 0 ? '+' : ''}{fmtK(displayNode.treasuryDelta)}
              </span>
            </div>
            <div className={styles.tooltipRow}>
              <span>Reputation Δ</span>
              <span className={`${styles.tooltipDelta} ${displayNode.repDelta >= 0 ? styles.tooltipDeltaUp : styles.tooltipDeltaDown}`}>
                {displayNode.repDelta >= 0 ? '+' : ''}{displayNode.repDelta.toFixed(1)}
              </span>
            </div>
            <div className={styles.tooltipRow}>
              <span>Carbon Δ</span>
              <span className={`${styles.tooltipDelta} ${displayNode.carbonDelta <= 0 ? styles.tooltipDeltaUp : styles.tooltipDeltaDown}`}>
                {displayNode.carbonDelta >= 0 ? '+' : ''}{(displayNode.carbonDelta / 1000).toFixed(1)}K tCO₂e
              </span>
            </div>
          </div>
        )}

        {/* Timeline Slider */}
        <div className={styles.timelineContainer}>
          <span className={styles.timelineLabel}>Timeline</span>
          <input
            type="range"
            className={styles.timelineSlider}
            min={1}
            max={Math.max(currentRound || 1, nodes.length)}
            value={timelineMax}
            onChange={(e) => setTimelineMax(parseInt(e.target.value, 10))}
          />
          <span className={styles.timelineValue}>R{timelineMax}</span>
        </div>

        {/* ESG Filter Bar */}
        <div className={styles.filterBar}>
          <span className={styles.filterLabel}>Filter</span>
          {[
            { key: 'all', label: 'All', color: '#5eead4' },
            { key: 'environmental', label: '🌱 E', color: ESG_COLORS.environmental },
            { key: 'social', label: '👥 S', color: ESG_COLORS.social },
            { key: 'governance', label: '🏛️ G', color: ESG_COLORS.governance },
          ].map(f => (
            <button
              key={f.key}
              className={`${styles.filterBtn} ${filter === f.key ? styles.filterBtnActive : ''}`}
              style={filter === f.key ? { borderColor: f.color, color: f.color, background: `${f.color}15` } : {}}
              onClick={() => setFilter(f.key)}
            >
              {f.label}
            </button>
          ))}
        </div>
      </div>
    </div>
  );
}
