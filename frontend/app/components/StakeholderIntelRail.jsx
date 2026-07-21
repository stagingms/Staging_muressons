// ─────────────────────────────────────────────────────────────────────────
// Slot (Player-UI V-D): RAIL TAB — "intel" (asynchronous context, one open at
// a time). The per-stakeholder relationship timeline opens in the EXPAND DRAWER.
// SPEC F6 (intent-forward UI): render what each stakeholder WANTS, how much
// LEVERAGE they hold, and which way the relationship is TRENDING — never the raw
// satisfaction/trust number (that stays in the facilitator/debrief view).
//
// This component is a thin consumer of the backend `extra.stakeholder_intel`
// payload emitted by npc_stakeholders.build_stakeholder_intel — the demand and
// leverage sentences are authored on the backend (single source of truth) so
// the front-end never re-implements them and the two cannot drift (SPEC §6.4).
// Uses semantic tone words (no raw hex for danger/success/caution) per repo
// tokens rules; swap the Tailwind classes for your token utilities when slotting.
// ─────────────────────────────────────────────────────────────────────────

import { useState } from "react";

// Escalation tier → semantic tone. Names vary per stakeholder (regulator uses
// "investigation", community uses "protest"), so map the known worst/better ones.
const TONE = {
  cooperative: "success", supportive: "success", satisfied: "success", favorable: "success",
  watchful: "neutral", concerned: "neutral", monitoring: "neutral", neutral: "neutral",
  protest: "caution", investigation: "caution", critical: "caution",
  legal: "danger", hostile: "danger", adversarial: "danger", enforcement: "danger",
};

const TONE_CLASSES = {
  success: "bg-green-50 text-green-800 border-green-200",
  neutral: "bg-slate-50 text-slate-700 border-slate-200",
  caution: "bg-amber-50 text-amber-800 border-amber-200",
  danger: "bg-red-50 text-red-800 border-red-200",
};

const TREND = {
  up: { glyph: "↑", label: "improving", cls: "text-green-700" },
  down: { glyph: "↓", label: "declining", cls: "text-red-700" },
  flat: { glyph: "→", label: "steady", cls: "text-slate-500" },
};

const SAMPLE = [
  {
    npc_id: "community_leader", name: "Rajesh Patil",
    title: "Head Panchayat, Deccan Plateau District Council", icon: "🏘️",
    escalation_level: "protest", demand: "wants stronger community license and local trust",
    leverage: { label: "high legitimacy, low power" }, trend: "declining", trend_direction: "down",
    facilitator: { satisfaction: 42.0, trust: 38.0 },
  },
  {
    npc_id: "regulator", name: "Commissioner Sofia Petrova",
    title: "EU DG FISMA — Corporate Sustainability Division", icon: "🏛️",
    escalation_level: "investigation", demand: "wants tighter governance and disclosure",
    leverage: { label: "high power, moderate urgency" }, trend: "steady", trend_direction: "flat",
    facilitator: { satisfaction: 36.0, trust: 44.0 },
  },
  {
    npc_id: "activist_investor", name: "Elise Thornton",
    title: "Managing Director, FutureFirst Activist Fund", icon: "🦅",
    escalation_level: "concerned", demand: "wants ESG-linked executive pay",
    leverage: { label: "high urgency, moderate legitimacy" }, trend: "improving", trend_direction: "up",
    facilitator: { satisfaction: 55.0, trust: 51.0 },
  },
];

export default function StakeholderIntelRail({ intel = SAMPLE, facilitator = false }) {
  const [openId, setOpenId] = useState(null); // one drawer open at a time

  return (
    <div className="w-full max-w-md text-sm">
      <div className="flex items-center justify-between px-1 pb-2">
        <h3 className="font-medium text-slate-800">Stakeholder intel</h3>
        <span className="text-xs text-slate-400">who wants what, and how hard they can push</span>
      </div>

      <ul className="space-y-2">
        {intel.map((s) => {
          const tone = TONE[s.escalation_level] || "neutral";
          const trend = TREND[s.trend_direction] || TREND.flat;
          const isOpen = openId === s.npc_id;
          return (
            <li key={s.npc_id} className="rounded-xl border border-slate-200 bg-white overflow-hidden">
              <button
                onClick={() => setOpenId(isOpen ? null : s.npc_id)}
                className="w-full text-left p-3 flex gap-3 items-start hover:bg-slate-50"
              >
                <span className="text-xl leading-none mt-0.5" aria-hidden>{s.icon}</span>
                <span className="flex-1 min-w-0">
                  <span className="flex items-center justify-between gap-2">
                    <span className="font-medium text-slate-800 truncate">{s.name}</span>
                    <span className={`shrink-0 text-xs px-2 py-0.5 rounded-full border ${TONE_CLASSES[tone]}`}>
                      {s.escalation_level}
                    </span>
                  </span>
                  <span className="block mt-1 text-slate-600">{s.demand}</span>
                  <span className="mt-1.5 flex items-center gap-3 text-xs text-slate-500">
                    <span>leverage: <span className="text-slate-700">{s.leverage?.label}</span></span>
                    <span className={trend.cls}>{trend.glyph} {trend.label}</span>
                  </span>
                </span>
              </button>

              {isOpen && (
                <div className="border-t border-slate-100 bg-slate-50 p-3 text-xs text-slate-600">
                  <div className="font-medium text-slate-700 mb-1">Relationship timeline</div>
                  <p className="text-slate-500">
                    Past actions and open promises for {s.name.split(" ")[0]} render here (expand-drawer
                    deep-dive). Wire to the promise ledger / interaction history.
                  </p>
                  {facilitator && s.facilitator && (
                    <div className="mt-2 pt-2 border-t border-slate-200 text-slate-500">
                      <span className="uppercase tracking-wide text-[10px] text-slate-400">Facilitator only</span>
                      <div>satisfaction {s.facilitator.satisfaction} · trust {s.facilitator.trust ?? "—"}</div>
                    </div>
                  )}
                </div>
              )}
            </li>
          );
        })}
      </ul>
    </div>
  );
}
