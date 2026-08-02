"""
Muressons Global Corporation — Side Track Registry & Dispatcher

Central registry for all side simulation tracks.
God Mode controls which tracks are globally available.
Facilitators assign available tracks to their cohorts.
"""

from __future__ import annotations
from typing import Any, Optional

from side_tracks.base_track import BaseSideTrack


# ═════════════════════════════════════════════════════════════════
#  TRACK REGISTRY
#  All side track implementations register themselves here.
#  Import order determines discovery order in the UI.
# ═════════════════════════════════════════════════════════════════

_REGISTRY: dict[str, BaseSideTrack] = {}


def register_track(track: BaseSideTrack) -> None:
    """Register a side track implementation."""
    if track.track_id in _REGISTRY:
        raise ValueError(f"Duplicate track_id: {track.track_id}")
    _REGISTRY[track.track_id] = track


def get_track(track_id: str) -> Optional[BaseSideTrack]:
    """Look up a registered track by ID."""
    return _REGISTRY.get(track_id)


def get_all_tracks() -> dict[str, BaseSideTrack]:
    """Return all registered tracks."""
    return dict(_REGISTRY)


def get_track_catalog() -> list[dict[str, Any]]:
    """
    Return a serialisable catalog of all registered tracks.
    Used by God Mode and Facilitator UIs to display available tracks.
    """
    catalog = []
    for tid, track in _REGISTRY.items():
        catalog.append({
            "track_id": tid,
            "display_name": track.display_name,
            "description": track.description,
            "icon": track.icon,
            "num_rounds": track.num_rounds,
            "available_window": list(track.available_window),
            "scoring_dimensions": track.scoring_dimensions,
            "cross_track_prerequisites": track.cross_track_prerequisites,
        })
    return catalog


# ═════════════════════════════════════════════════════════════════
#  AUTO-REGISTRATION
#  Import track modules to trigger their registration.
# ═════════════════════════════════════════════════════════════════

from side_tracks.supply_chain import SupplyChainTrack
from side_tracks.ethics_sustainability import EthicsSustainabilityTrack
from side_tracks.stakeholder_management import StakeholderManagementTrack
from side_tracks.sustainability_reporting import SustainabilityReportingTrack
from side_tracks.corporate_sdg import CorporateSDGTrack
from side_tracks.brsr_ngrbc import BRSRNGRBCTrack

register_track(SupplyChainTrack())
register_track(EthicsSustainabilityTrack())
register_track(StakeholderManagementTrack())
register_track(SustainabilityReportingTrack())
register_track(CorporateSDGTrack())
register_track(BRSRNGRBCTrack())
