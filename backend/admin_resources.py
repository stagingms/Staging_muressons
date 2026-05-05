"""
Muressons Global Corporation - Admin Resources Sub-Router (ARCH-002)
Extracted from admin_router.py to reduce monolith size.

Contains:
  - Resource Library (master library CRUD, per-session unlock/drop/lock)
  - Hidden Resource Trigger Engine
  - Facilitator Deployment Guide
  - NotebookLM Integration (notebook CRUD + podcast data)
  - Quiz Difficulty & Per-Cohort Quiz/Consultant Settings
  - 18 API endpoints
"""
from __future__ import annotations

import os
import shutil
import json
from typing import Optional
from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException, UploadFile, File, Body
from pydantic import BaseModel

import database as db

resources_router = APIRouter(prefix="/api/admin", tags=["Admin - Resources"])

# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
#  RESOURCE LIBRARY â€” Master Library + Per-Session Unlock Control
# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•

class ResourceUnlockCondition(BaseModel):
    metric: str = ""           # e.g. "Investment_E5", "G1_Score", "BU_Sustainability_Score"
    operator: str = ">="       # ">=", "<=", "==", ">", "<"
    value: float = 0
    min_round: int = 1         # Minimum round before condition can trigger

class ResourceEffect(BaseModel):
    target: str = ""           # e.g. "Electronics_OpEx", "S2_Financial_Risk"
    modifier: float = 0        # e.g. -0.10 for 10% reduction

class ResourceItem(BaseModel):
    id: str
    title: str
    type: str  # "PDF" | "Video" | "Weblink" | "Memo" | "NotebookLM"
    url: str = ""
    tags: list[str] = []
    category: str = "General"  # "Ecological" | "Social" | "Economic" | "General"
    facilitator_default_round: int = 1
    impact_link: str = ""
    visibility: str = "Standard"  # "Standard" | "Hidden"
    unlock_condition: Optional[dict] = None  # {metric, operator, value, min_round}
    effect: Optional[dict] = None            # {target, modifier}
    facilitator_strategy: str = ""           # Deployment hint for facilitator cheat sheet

class ResourceLibraryUpload(BaseModel):
    Resource_Library: list[ResourceItem]

class ResourceUnlockRequest(BaseModel):
    resource_ids: list[str]
    round_number: int

# â”€â”€ In-memory stores â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

_resource_library: list[dict] = [
    # â”€â”€ Standard Resources â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
    {
        "id": "RES_001",
        "title": "The ESRS Double Materiality Handbook",
        "type": "PDF",
        "url": "https://antigravity-sim.com/docs/esrs_handbook.pdf",
        "tags": ["General", "CSRD"],
        "category": "General",
        "facilitator_default_round": 1,
        "impact_link": "",
        "visibility": "Standard",
        "unlock_condition": None,
        "effect": None,
        "facilitator_strategy": "The Baseline: Drop immediately. Sets the rules. Players who skip this will fail to understand the Volatility factor.",
    },
    {
        "id": "RES_002",
        "title": "Pharma Wastewater Standards 2026",
        "type": "Weblink",
        "url": "https://epa.gov/pharma-standards",
        "tags": ["Pharma", "E2"],
        "category": "Ecological",
        "facilitator_default_round": 4,
        "impact_link": "E2 (Pharma)",
        "visibility": "Standard",
        "unlock_condition": None,
        "effect": None,
        "facilitator_strategy": "Drop in Round 4 to coincide with ESG Contagion Crisis. Forces Pharma BU investment decisions.",
    },
    {
        "id": "RES_003",
        "title": "Global Carbon Tax Forecast (2026-2030)",
        "type": "PDF",
        "url": "https://antigravity-sim.com/docs/carbon_tax_forecast.pdf",
        "tags": ["General", "E1", "Climate"],
        "category": "Ecological",
        "facilitator_default_round": 3,
        "impact_link": "E1 (All BUs)",
        "visibility": "Standard",
        "unlock_condition": None,
        "effect": None,
        "facilitator_strategy": "The Warning: Drop in Round 3 to force players to choose between short-term dividends and E1 (Climate) investments.",
    },
    {
        "id": "RES_004",
        "title": "Gobi Region Mineral Conflict Map",
        "type": "PDF",
        "url": "https://antigravity-sim.com/docs/gobi_conflict_map.pdf",
        "tags": ["Electronics", "S2", "Labor"],
        "category": "Social",
        "facilitator_default_round": 5,
        "impact_link": "S2 (Electronics)",
        "visibility": "Standard",
        "unlock_condition": None,
        "effect": None,
        "facilitator_strategy": "The Crisis Catalyst: Drop 1 turn before the embargo. If they don't act on this info, they deserve the 30% COGS hike.",
    },
    {
        "id": "RES_005",
        "title": "GDPR 2026 Compliance Brief",
        "type": "PDF",
        "url": "https://antigravity-sim.com/docs/gdpr_2026.pdf",
        "tags": ["Software", "S4", "Privacy"],
        "category": "Social",
        "facilitator_default_round": 3,
        "impact_link": "S4 (Software)",
        "visibility": "Standard",
        "unlock_condition": None,
        "effect": None,
        "facilitator_strategy": "",
    },
    {
        "id": "RES_006",
        "title": "The Business of Urban Mining",
        "type": "Video",
        "url": "https://youtube.com/antigravity_urban_mining",
        "tags": ["Electronics", "E5", "Circularity"],
        "category": "Ecological",
        "facilitator_default_round": 6,
        "impact_link": "E5 (Conglomerate)",
        "visibility": "Standard",
        "unlock_condition": None,
        "effect": None,
        "facilitator_strategy": "",
    },
    {
        "id": "RES_007",
        "title": "API Effluent Technical Guide",
        "type": "Weblink",
        "url": "https://antigravity-sim.com/docs/api_effluent_guide",
        "tags": ["Pharma", "E2", "Pollution"],
        "category": "Ecological",
        "facilitator_default_round": 4,
        "impact_link": "E2 (Pharma)",
        "visibility": "Standard",
        "unlock_condition": None,
        "effect": None,
        "facilitator_strategy": "",
    },
    {
        "id": "RES_008",
        "title": "Gobi Region Human Rights Map",
        "type": "PDF",
        "url": "https://antigravity-sim.com/docs/gobi_human_rights.pdf",
        "tags": ["Electronics", "S2", "Labor"],
        "category": "Social",
        "facilitator_default_round": 5,
        "impact_link": "S2 (Electronics)",
        "visibility": "Standard",
        "unlock_condition": None,
        "effect": None,
        "facilitator_strategy": "",
    },
    # â”€â”€ Hidden Resources (Auto-Unlock via Conditions) â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
    {
        "id": "HIDDEN_RES_001",
        "title": "The Urban Mining Efficiency Secret",
        "type": "Video",
        "url": "https://antigravity-sim.com/hidden/urban_mining_secret",
        "tags": ["Electronics", "E5", "Circularity"],
        "category": "Ecological",
        "facilitator_default_round": 0,
        "impact_link": "E5 (Electronics)",
        "visibility": "Hidden",
        "unlock_condition": {"metric": "Investment_E5", "operator": ">=", "value": 150_000_000, "min_round": 1},
        "effect": {"target": "Electronics_OpEx", "modifier": -0.10},
        "facilitator_strategy": "Investment reward: Unlocks when team invests $150M+ in Electronics. Reduces future Electronics BU upgrade costs by 10%.",
    },
    {
        "id": "HIDDEN_RES_002",
        "title": "Whistleblower Brief: Gobi Mine Ethics",
        "type": "Memo",
        "url": "",
        "tags": ["Electronics", "S2", "Governance"],
        "category": "Social",
        "facilitator_default_round": 0,
        "impact_link": "S2 (Electronics)",
        "visibility": "Hidden",
        "unlock_condition": {"metric": "G1_Score", "operator": "==", "value": 10, "min_round": 1},
        "effect": {"target": "S2_Financial_Risk", "modifier": -0.50},
        "facilitator_strategy": "Governance reward: Unlocks when G1 Ethics Score reaches 10. Halves financial risk from S2 labor issues.",
    },
    {
        "id": "HIDDEN_RES_003",
        "title": "Bio-Safe API Manufacturing Patent",
        "type": "PDF",
        "url": "https://antigravity-sim.com/hidden/biosafe_patent.pdf",
        "tags": ["Pharma", "E2"],
        "category": "Ecological",
        "facilitator_default_round": 0,
        "impact_link": "E2 (Pharma)",
        "visibility": "Hidden",
        "unlock_condition": {"metric": "Pharma_E2_Score", "operator": ">=", "value": 8.5, "min_round": 4},
        "effect": {"target": "Pharma_Contract", "modifier": 200_000_000},
        "facilitator_strategy": "Sustainability reward: Unlocks when Pharma E2 score reaches 8.5+. Grants access to a $200M government contract in Round 8.",
    },
    {
        "id": "HIDDEN_RES_004",
        "title": "The Ethical AI Advantage",
        "type": "Memo",
        "url": "",
        "tags": ["Software", "G1", "AI"],
        "category": "Economic",
        "facilitator_default_round": 0,
        "impact_link": "G1 (Software)",
        "visibility": "Hidden",
        "unlock_condition": {"metric": "Software_G1_Score", "operator": "==", "value": 10, "min_round": 1},
        "effect": {"target": "Data_Breach_Prevention", "modifier": 1},
        "facilitator_strategy": "Risk mitigation: Unlocks when Software G1 score reaches 10. Prevents the Data Breach event from triggering.",
    },
]

# session_id â†’ list of {resource_id, unlocked_at_round, unlocked_at_time, is_strategic_drop, trigger}
_session_resource_state: dict[str, list[dict]] = {}


# â”€â”€ Hidden Resource Trigger Engine â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

def _extract_metric_value(metric: str, global_state: dict, bu_states: list[dict]) -> Optional[float]:
    """Extract a metric value from game state for hidden resource condition evaluation."""
    # Investment-based metrics (cumulative capex allocated to a BU category)
    if metric.startswith("Investment_"):
        bu_key = metric.replace("Investment_", "").lower()
        # Map E5 â†’ electronics, etc.
        bu_map = {"e5": "electronics", "e1": "pharma", "e2": "pharma", "s2": "electronics", "g1": "software"}
        target_bu = bu_map.get(bu_key, bu_key)
        bu = next((b for b in bu_states if b["bu_id"] == target_bu), None)
        if bu:
            # Use cumulative investment tracked in active_event_flags
            flags = global_state.get("active_event_flags", {})
            return flags.get(f"cumulative_investment_{target_bu}", 0)
        return 0

    # BU-specific sustainability/score metrics
    if metric == "G1_Score":
        sw = next((b for b in bu_states if b["bu_id"] == "software"), None)
        return (10 - sw.get("governance_risk_score", 10)) if sw else 0

    if metric == "Software_G1_Score":
        sw = next((b for b in bu_states if b["bu_id"] == "software"), None)
        return (10 - sw.get("governance_risk_score", 10)) if sw else 0

    if metric == "Pharma_E2_Score":
        pharma = next((b for b in bu_states if b["bu_id"] == "pharma"), None)
        if pharma:
            # Derive E2 score from social license and natural capital debt inversely
            sl = pharma.get("social_license_score", 50)
            return sl / 10.0  # Normalize 0-100 â†’ 0-10 scale
        return 0

    if metric == "BU_Sustainability_Score":
        avg_sl = sum(b.get("social_license_score", 50) for b in bu_states) / len(bu_states) if bu_states else 50
        return avg_sl / 10.0  # Normalize to 0-10 scale

    # Generic global state lookup
    return global_state.get(metric, 0)


def _evaluate_condition(actual: float, operator: str, target: float) -> bool:
    """Evaluate a single condition: actual <op> target."""
    if operator == ">=": return actual >= target
    if operator == "<=": return actual <= target
    if operator == "==": return actual == target
    if operator == ">":  return actual > target
    if operator == "<":  return actual < target
    return False


async def check_hidden_resource_triggers(
    session_id: str,
    round_number: int,
    global_state: dict,
    bu_states: list[dict],
) -> list[dict]:
    """
    Evaluate all hidden resources against current game state.
    Auto-unlocks any that meet their conditions.
    Returns list of newly unlocked hidden resources.
    """
    if session_id not in _session_resource_state:
        _session_resource_state[session_id] = []

    existing_ids = {u["resource_id"] for u in _session_resource_state[session_id]}
    newly_triggered = []

    for res in _resource_library:
        if res.get("visibility") != "Hidden":
            continue
        if res["id"] in existing_ids:
            continue  # Already unlocked

        cond = res.get("unlock_condition")
        if not cond:
            continue

        # Check min_round
        if round_number < cond.get("min_round", 1):
            continue

        # Extract and evaluate
        actual = _extract_metric_value(cond["metric"], global_state, bu_states)
        if actual is None:
            continue

        if _evaluate_condition(actual, cond["operator"], cond["value"]):
            entry = {
                "resource_id": res["id"],
                "unlocked_at_round": round_number,
                "unlocked_at_time": datetime.now(timezone.utc).isoformat(),
                "is_strategic_drop": False,
                "trigger": "auto_condition",
            }
            _session_resource_state[session_id].append(entry)
            newly_triggered.append(res)

    # Notify facilitator and players about auto-unlocked hidden resources
    if newly_triggered:
        await manager.push_to_session(session_id, {
            "type": "resource_unlocked",
            "resources": newly_triggered,
            "round": round_number,
            "is_hidden_unlock": True,
        })
        await manager.broadcast_admin({
            "type": "hidden_resource_triggered",
            "session_id": session_id,
            "resources": [{"id": r["id"], "title": r["title"], "effect": r.get("effect")} for r in newly_triggered],
            "round": round_number,
        })

    return newly_triggered


# â”€â”€ Facilitator Deployment Guide â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

FACILITATOR_DEPLOYMENT_GUIDE = [
    {"round": 1, "resource_id": "RES_001", "strategy": "The Baseline: Drop immediately. It sets the rules. If players don't read this, they will fail to understand the Volatility factor."},
    {"round": 3, "resource_id": "RES_003", "strategy": "The Warning: Drop to force players to choose between short-term dividends and E1 (Climate) investments."},
    {"round": 3, "resource_id": "RES_005", "strategy": "Supplement the Decision Tab. GDPR compliance context for Software BU decisions."},
    {"round": 4, "resource_id": "RES_002", "strategy": "Coincides with ESG Contagion Crisis. Forces Pharma BU investment decisions."},
    {"round": 4, "resource_id": "RES_007", "strategy": "Technical context for Pharma pollution decisions."},
    {"round": 5, "resource_id": "RES_004", "strategy": "The Crisis Catalyst: Drop 1 turn before the embargo. If they don't act on this info, they deserve the 30% COGS hike."},
    {"round": 5, "resource_id": "RES_008", "strategy": "Supplement the Gobi crisis with human rights context."},
    {"round": 6, "resource_id": "RES_006", "strategy": "Circular Economy context for Round 6 pivot decisions."},
]

@resources_router.get("/resources/deployment-guide", summary="Get the facilitator deployment guide")
async def get_deployment_guide():
    """Returns the round-by-round resource deployment cheat sheet."""
    # Enrich with resource titles
    guide = []
    for entry in FACILITATOR_DEPLOYMENT_GUIDE:
        res = next((r for r in _resource_library if r["id"] == entry["resource_id"]), None)
        guide.append({
            **entry,
            "title": res["title"] if res else "Unknown",
            "type": res["type"] if res else "",
        })

    # Add hidden resource guide
    hidden_guide = []
    for res in _resource_library:
        if res.get("visibility") == "Hidden":
            hidden_guide.append({
                "resource_id": res["id"],
                "title": res["title"],
                "unlock_condition": res.get("unlock_condition"),
                "effect": res.get("effect"),
                "strategy": res.get("facilitator_strategy", ""),
            })

    return {
        "round_deployment": guide,
        "hidden_resources": hidden_guide,
    }



# â”€â”€ Master Library CRUD â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

@resources_router.get("/resources/library", summary="Get the master resource library")
async def get_resource_library():
    return {"resources": _resource_library}


@resources_router.put("/resources/library", summary="Upload / replace the master resource library")
async def upload_resource_library(body: ResourceLibraryUpload):
    global _resource_library
    _resource_library = [r.dict() for r in body.Resource_Library]
    return {"status": "uploaded", "count": len(_resource_library)}


@resources_router.post("/resources/library/item", summary="Add or update a single resource")
async def upsert_resource_item(item: ResourceItem):
    global _resource_library
    _resource_library = [r for r in _resource_library if r["id"] != item.id]
    _resource_library.append(item.dict())
    return item


@resources_router.delete("/resources/library/item/{resource_id}", summary="Delete a resource from the master library")
async def delete_resource_item(resource_id: str):
    global _resource_library
    _resource_library = [r for r in _resource_library if r["id"] != resource_id]
    return {"status": "deleted", "resource_id": resource_id}


@resources_router.post("/resources/upload", summary="Upload a physical resource file (PDF, image, etc)")
async def upload_resource_file(file: UploadFile = File(...)):
    """Uploads a file to the static assets directory and returns its public URL."""
    # Ensure uploads directory exists in the Next.js frontend/public folder
    project_root = os.path.dirname(os.path.dirname(__file__))
    upload_dir = os.path.join(project_root, "frontend", "public", "uploads")
    os.makedirs(upload_dir, exist_ok=True)
    
    # Save the file
    file_path = os.path.join(upload_dir, file.filename)
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
        
    # Return the URL path
    file_url = f"/uploads/{file.filename}"
    return {"status": "uploaded", "url": file_url}


# â”€â”€ Per-Session Resource State â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

@resources_router.get("/sessions/{session_id}/resources", summary="Get resource state for a session")
async def get_session_resources(session_id: str):
    """Returns the master library annotated with unlock status for this session."""
    unlocked = _session_resource_state.get(session_id, [])
    unlocked_ids = {u["resource_id"] for u in unlocked}

    annotated = []
    for res in _resource_library:
        unlock_info = next((u for u in unlocked if u["resource_id"] == res["id"]), None)
        annotated.append({
            **res,
            "unlocked": res["id"] in unlocked_ids,
            "unlocked_at_round": unlock_info["unlocked_at_round"] if unlock_info else None,
            "unlocked_at_time": unlock_info["unlocked_at_time"] if unlock_info else None,
            "is_strategic_drop": unlock_info.get("is_strategic_drop", False) if unlock_info else False,
        })
    return {"resources": annotated}


@resources_router.post("/sessions/{session_id}/resources/unlock", summary="Unlock resources for a session")
async def unlock_session_resources(session_id: str, body: ResourceUnlockRequest):
    """Unlock specific resources for a session at a given round."""
    if session_id not in _session_resource_state:
        _session_resource_state[session_id] = []

    existing_ids = {u["resource_id"] for u in _session_resource_state[session_id]}
    newly_unlocked = []
    for rid in body.resource_ids:
        if rid not in existing_ids:
            entry = {
                "resource_id": rid,
                "unlocked_at_round": body.round_number,
                "unlocked_at_time": datetime.now(timezone.utc).isoformat(),
                "is_strategic_drop": False,
            }
            _session_resource_state[session_id].append(entry)
            newly_unlocked.append(rid)

    # Build full resource objects for the push
    unlocked_resources = [r for r in _resource_library if r["id"] in newly_unlocked]

    # Push to players via WebSocket
    if newly_unlocked:
        await manager.push_to_session(session_id, {
            "type": "resource_unlocked",
            "resources": unlocked_resources,
            "round": body.round_number,
        })

    return {"status": "unlocked", "newly_unlocked": newly_unlocked, "total_unlocked": len(_session_resource_state[session_id])}


@resources_router.post("/sessions/{session_id}/resources/drop", summary="Strategic drop â€” reveal a resource mid-round")
async def strategic_drop_resource(session_id: str, body: ResourceUnlockRequest):
    """Drops resources mid-round as a 'breaking news' event. Marks them as strategic drops."""
    if session_id not in _session_resource_state:
        _session_resource_state[session_id] = []

    existing_ids = {u["resource_id"] for u in _session_resource_state[session_id]}
    dropped = []
    for rid in body.resource_ids:
        if rid not in existing_ids:
            entry = {
                "resource_id": rid,
                "unlocked_at_round": body.round_number,
                "unlocked_at_time": datetime.now(timezone.utc).isoformat(),
                "is_strategic_drop": True,
            }
            _session_resource_state[session_id].append(entry)
            dropped.append(rid)

    dropped_resources = [r for r in _resource_library if r["id"] in dropped]

    if dropped:
        await manager.push_to_session(session_id, {
            "type": "resource_dropped",
            "resources": dropped_resources,
            "round": body.round_number,
            "is_breaking_news": True,
        })
        await manager.broadcast_admin({
            "type": "resource_strategic_drop",
            "session_id": session_id,
            "resources": dropped_resources,
        })

    return {"status": "dropped", "dropped": dropped}


@resources_router.post("/sessions/{session_id}/resources/lock", summary="Re-lock a resource for a session")
async def lock_session_resource(session_id: str, body: dict = Body(...)):
    """Re-lock a mistakenly unlocked resource."""
    resource_id = body.get("resource_id")
    if not resource_id:
        raise HTTPException(400, "resource_id required")
    if session_id in _session_resource_state:
        _session_resource_state[session_id] = [
            u for u in _session_resource_state[session_id] if u["resource_id"] != resource_id
        ]
    return {"status": "locked", "resource_id": resource_id}


# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
#  NOTEBOOKLM INTEGRATION â€” Linked Notebooks for Learners
# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•

class NotebookLMItem(BaseModel):
    id: str
    title: str
    share_url: str = ""
    description: str = ""
    content_types: list[str] = ["review"]  # "podcast" | "review" | "quiz"
    target_round: int = 1  # Round this notebook becomes available
    category: str = "General"  # "General" | "Ecological" | "Social" | "Economic"
    podcast_transcript: list[dict] = []  # [{speaker, text}, ...]
    review_content: str = ""  # Markdown-style review content
    quiz_questions: list[dict] = []  # [{question, options, correct, explanation}, ...]

# In-memory store for linked NotebookLM notebooks
from quiz_banks import (
    NLM_001_REVIEW, NLM_001_QUESTIONS,
    NLM_002_REVIEW, NLM_002_QUESTIONS,
    NLM_003_REVIEW, NLM_003_QUESTIONS,
)

_notebooklm_notebooks: list[dict] = [
    {
        "id": "NLM_001",
        "title": "ESG Fundamentals Deep Dive",
        "share_url": "",
        "description": "Interactive review of ESG concepts, CSRD requirements, and double materiality. Includes an AI-generated podcast overview.",
        "content_types": ["podcast", "review", "quiz"],
        "target_round": 1,
        "category": "General",
        "podcast_transcript": [
            {"speaker": "Dr. Priya Sharma", "text": "Welcome to the ESG Fundamentals podcast. Today we're breaking down what every executive needs to know about Environmental, Social, and Governance factors."},
            {"speaker": "Prof. James Walker", "text": "Great to be here, Priya. Let's start with the basics. ESG isn't just a compliance checkbox â€” it's become a core driver of corporate value creation."},
            {"speaker": "Dr. Priya Sharma", "text": "Exactly. The E stands for Environmental â€” think carbon emissions, water usage, waste management, and biodiversity impact. Companies like Muressons with mining and manufacturing operations face significant environmental scrutiny."},
            {"speaker": "Prof. James Walker", "text": "The S covers Social factors â€” labour practices, community relations, diversity, supply chain ethics. For a conglomerate operating across regions like Gobi and Deccan, this is critical."},
            {"speaker": "Dr. Priya Sharma", "text": "And G â€” Governance â€” covers board composition, executive pay, transparency, and anti-corruption measures. Strong governance is the foundation that makes E and S credible."},
            {"speaker": "Prof. James Walker", "text": "Now, let's talk about Double Materiality. Under the EU's CSRD directive, companies must report on two dimensions: how sustainability issues affect the company financially, AND how the company impacts society and the environment."},
            {"speaker": "Dr. Priya Sharma", "text": "This is a paradigm shift. Traditional financial materiality only asked 'does this risk affect our bottom line?' Double materiality also asks 'does our business affect the planet and people?'"},
            {"speaker": "Prof. James Walker", "text": "For Muressons, this means mapping every business unit â€” Pharma, Electronics, Consumer Goods, Software â€” against both dimensions. The ESG audit in Round 1 is your first step."},
            {"speaker": "Dr. Priya Sharma", "text": "Key takeaway: ESG integration isn't optional anymore. Investors, regulators, and consumers are all demanding it. The companies that lead on ESG will have a competitive advantage in the 2030s."},
            {"speaker": "Prof. James Walker", "text": "Absolutely. And remember â€” the depth of your initial audit determines what risks you catch early versus what surprises you later. Choose wisely."},
        ],
        "review_content": NLM_001_REVIEW,
        "quiz_questions": NLM_001_QUESTIONS,
    },
    {
        "id": "NLM_002",
        "title": "Carbon Markets & Climate Risk",
        "share_url": "",
        "description": "Deep dive into carbon pricing mechanisms, EU ETS, emission scopes, and corporate climate strategy.",
        "content_types": ["quiz", "review"],
        "target_round": 3,
        "category": "Ecological",
        "podcast_transcript": [],
        "review_content": NLM_002_REVIEW,
        "quiz_questions": NLM_002_QUESTIONS,
    },
    {
        "id": "NLM_003",
        "title": "Supply Chain Ethics & Labour Rights",
        "share_url": "",
        "description": "Explore the Gobi region conflict, modern slavery legislation, and due diligence frameworks through AI-guided review.",
        "content_types": ["podcast", "review", "quiz"],
        "target_round": 5,
        "category": "Social",
        "podcast_transcript": [
            {"speaker": "Dr. Priya Sharma", "text": "Today we're tackling one of the most challenging aspects of ESG â€” supply chain ethics and labour rights. This is deeply relevant to Muressons' operations in the Gobi region."},
            {"speaker": "Prof. James Walker", "text": "Absolutely. The Gobi region represents a classic ethical dilemma in global supply chains. Rich mineral resources, but significant human rights concerns."},
            {"speaker": "Dr. Priya Sharma", "text": "Let's frame the issue. Modern slavery affects an estimated 50 million people globally. Forced labour generates $150 billion in illegal profits annually. And it's not just in developing countries â€” it exists in every sector."},
            {"speaker": "Prof. James Walker", "text": "For mining operations like those in the Gobi region, the risks include: forced labour in artisanal mining, child labour, dangerous working conditions, and community displacement."},
            {"speaker": "Dr. Priya Sharma", "text": "Several key pieces of legislation now require companies to act. The UK Modern Slavery Act, the French Duty of Vigilance Law, and the proposed EU Corporate Sustainability Due Diligence Directive."},
            {"speaker": "Prof. James Walker", "text": "The EU CSDDD is particularly important. It requires companies to identify, prevent, and mitigate adverse human rights and environmental impacts throughout their value chains."},
            {"speaker": "Dr. Priya Sharma", "text": "So what should Muressons do? First, conduct thorough supply chain mapping. Know every tier of your suppliers. Second, implement robust due diligence processes. Third, establish grievance mechanisms for workers."},
            {"speaker": "Prof. James Walker", "text": "And critically, don't just cut and run from problematic suppliers. Responsible disengagement means working with suppliers to improve, not abandoning workers to worse conditions."},
            {"speaker": "Dr. Priya Sharma", "text": "The business case is clear too. Companies with strong supply chain ethics see fewer disruptions, better brand reputation, and increasingly, better access to capital."},
            {"speaker": "Prof. James Walker", "text": "Bottom line: in the Muressons simulation, your choices about the Gobi region and Tier-3 mine workers aren't just ethical decisions â€” they're strategic ones that affect your reputation score, regulatory risk, and long-term viability."},
        ],
        "review_content": NLM_003_REVIEW,
        "quiz_questions": NLM_003_QUESTIONS,
    },
]


@resources_router.get("/resources/notebooklm", summary="Get all linked NotebookLM notebooks")
async def get_notebooklm_notebooks():
    return {"notebooks": _notebooklm_notebooks}


@resources_router.post("/resources/notebooklm", summary="Add or update a NotebookLM notebook link")
async def upsert_notebooklm_notebook(item: NotebookLMItem):
    global _notebooklm_notebooks
    _notebooklm_notebooks = [n for n in _notebooklm_notebooks if n["id"] != item.id]
    _notebooklm_notebooks.append(item.dict())
    return item


@resources_router.delete("/resources/notebooklm/{notebook_id}", summary="Remove a NotebookLM notebook link")
async def delete_notebooklm_notebook(notebook_id: str):
    global _notebooklm_notebooks
    _notebooklm_notebooks = [n for n in _notebooklm_notebooks if n["id"] != notebook_id]
    return {"status": "deleted", "notebook_id": notebook_id}


# â”€â”€ Quiz Difficulty Setting â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

_quiz_difficulty: str = "medium"  # "easy" | "medium" | "hard"


@resources_router.get("/quiz-difficulty", summary="Get current quiz difficulty level")
async def get_quiz_difficulty():
    return {"difficulty": _quiz_difficulty}


@resources_router.put("/quiz-difficulty", summary="Set quiz difficulty level")
async def set_quiz_difficulty(body: dict = Body(...)):
    global _quiz_difficulty
    level = body.get("difficulty", "medium").lower()
    if level not in ("easy", "medium", "hard"):
        raise HTTPException(400, "Difficulty must be 'easy', 'medium', or 'hard'")
    _quiz_difficulty = level
    return {"status": "updated", "difficulty": _quiz_difficulty}


# â”€â”€ Per-Cohort Quiz Enabled State â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

_quiz_enabled: dict[str, bool] = {}  # session_id â†’ enabled (default True)


@resources_router.get("/quiz-enabled/{session_id}", summary="Check if quiz is enabled for a cohort")
async def get_quiz_enabled(session_id: str):
    enabled = _quiz_enabled.get(session_id, True)  # Default: enabled
    return {"session_id": session_id, "quiz_enabled": enabled}


@resources_router.put("/quiz-enabled/{session_id}", summary="Enable or disable quiz for a cohort")
async def set_quiz_enabled(session_id: str, body: dict = Body(...)):
    enabled = body.get("quiz_enabled", True)
    _quiz_enabled[session_id] = bool(enabled)
    return {"status": "updated", "session_id": session_id, "quiz_enabled": _quiz_enabled[session_id]}


# â”€â”€ Per-Cohort Consultant Allowed State â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

_consultant_allowed: dict[str, bool] = {}  # session_id â†’ allowed (default True)


@resources_router.get("/consultant-allowed/{session_id}", summary="Check if ESG consultant is allowed for a cohort")
async def get_consultant_allowed(session_id: str):
    allowed = _consultant_allowed.get(session_id, True)  # Default: allowed
    return {"session_id": session_id, "consultant_allowed": allowed}


@resources_router.put("/consultant-allowed/{session_id}", summary="Enable or disable ESG consultant for a cohort")
async def set_consultant_allowed(session_id: str, body: dict = Body(...)):
    allowed = body.get("consultant_allowed", True)
    _consultant_allowed[session_id] = bool(allowed)
    return {"status": "updated", "session_id": session_id, "consultant_allowed": _consultant_allowed[session_id]}

