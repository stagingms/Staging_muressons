"""roster_shape.py — one cohort, one roster shape, resolved from formation data.

WHY THIS MODULE EXISTS
----------------------
A player roster is not one shape, because a cohort is not one thing.

  * 4-BU CONGLOMERATE — every player runs the whole group: four business units,
    one balance sheet. A player row that names a business unit is not merely
    redundant here, it is actively WRONG. join_session treats a per-player
    `assigned_bu` as Priority 1 and create_session then filters that player's
    bu_states down to the one named BU, so a conglomerate roster carrying
    assigned_bu silently produces N single-BU players who each believe they are
    running a group. Nothing errors and nothing looks broken; the cohort is
    simply not the cohort the facilitator formed. So in this shape those
    columns DO NOT EXIST, and naming one is an upload error that says why.

  * SINGLE BUSINESS — each player runs their OWN company. `industry_vertical`
    and `region_id` are precisely the two facts that make one player's run
    differ from another's, so both are per-row, and both are picked from the
    cohort's formation vocabulary rather than typed from memory.

`assigned_bu` is never authored in EITHER shape. It is the seed SLOT that owns
the chosen vertical, derived here through the same VERTICAL_SLOT_MAP that
/simulations/start and join_session already use. Letting an author write both
invites a row saying industry_vertical=oil_gas, assigned_bu=software, and no
reading of that row is defensible — so the sheet carries the fact the author
actually knows (the industry) and the server derives the mechanism.

THREE CONSUMERS, ONE SHAPE
--------------------------
    build_player_template          headers, dropdowns, the 'How to use' sheet
    parse_player_sheet             accepted columns, refused columns, whitelists
    GET .../players/roster-shape   the modal's copy, preview columns, hints

All three read the SAME object, so the spreadsheet cannot offer a value the
parser rejects, and the modal cannot describe a column the template does not
ship. This extends the pattern excel_dropdowns.py already established for the
facilitator template — catalogues DERIVED from the authoritative source, never
retyped — from "which values are legal" to "which columns exist at all".

BLANK MEANS INHERIT
-------------------
In single-business mode a blank industry or region falls back to the cohort's
own formation value rather than erroring. A facilitator who wants one shared
market leaves both columns alone; one who wants players competing across
industries or geographies fills them in. Both readings of a blank cell are
defensible, so the resolved value is echoed in the preview before anything is
created — the operator never has to guess which one the server chose.

VOCABULARY PROVENANCE (all fail-open — a template download must never 500)
    verticals  router.VERTICAL_SLOT_MAP, the same map that resolves a vertical
               to its seed slot at cohort start and at join time.
    regions    excel_dropdowns.region_ids() -> regional_reporting, the six
               regions the Create-Cohort form offers.
"""
from __future__ import annotations

from dataclasses import dataclass

# ── Modes ───────────────────────────────────────────────────────────────────
CONGLOMERATE = "conglomerate"
SINGLE_BU = "single_bu"

# `simulation_mode` is an overloaded key: the Switchboard also writes climate
# branch values ("standard", "advanced_climate") into it. Only "single_bu" ever
# means single-business, so everything else — including a blank, which is what a
# cohort created before the field existed carries — is the conglomerate.
def normalise_mode(raw) -> str:
    return SINGLE_BU if str(raw or "").strip().lower() == SINGLE_BU else CONGLOMERATE


# ── Column vocabulary ───────────────────────────────────────────────────────
NAME = "name"
EMAIL = "email"
PROGRAMME = "programme"
INDUSTRY = "industry_vertical"
REGION = "region_id"
ASSIGNED_BU = "assigned_bu"

_IDENTITY_COLUMNS = (NAME, EMAIL, PROGRAMME)
_SCOPE_COLUMNS = (INDUSTRY, REGION)

# Every column a roster sheet could plausibly carry. The parser reads the header
# row against this set to tell "a column I refuse in this mode" apart from "an
# institution's own bookkeeping column", which is ignored rather than rejected.
KNOWN_COLUMNS = _IDENTITY_COLUMNS + _SCOPE_COLUMNS + (ASSIGNED_BU,)

# Refusals are phrased for the person holding the spreadsheet, not the reviewer
# holding the diff: what is wrong, why it is wrong for THIS cohort, and what to
# do instead. A refusal with no remedy just moves the confusion.
_REFUSAL_CONGLOMERATE = {
    ASSIGNED_BU: (
        "'{col}' is not a column on a 4-BU conglomerate roster — every player "
        "in this cohort runs all four business units. Delete the column: "
        "assigning one BU per player would quietly scope each player down to a "
        "single business, which is the Single Business mode, not this one."
    ),
    INDUSTRY: (
        "'{col}' is not a per-player column on a 4-BU conglomerate roster — the "
        "four verticals are fixed for the whole cohort in the Industry "
        "Verticals tab of Edit Cohort. Delete the column."
    ),
    REGION: (
        "'{col}' is not a per-player column on a 4-BU conglomerate roster — "
        "region is set for the cohort, and per-BU in Multi-Region cohorts, in "
        "Edit Cohort. Delete the column."
    ),
}
_REFUSAL_SINGLE_BU = {
    ASSIGNED_BU: (
        "'{col}' is never authored — the business-unit slot is derived from "
        "'industry_vertical'. Delete the column and name the industry instead, "
        "so the two can never contradict each other."
    ),
}


@dataclass(frozen=True)
class RosterShape:
    """The shape of one cohort's player roster. Immutable: it is a projection of
    formation data, so a caller that wants a different shape must resolve a
    different cohort rather than mutate this one."""

    mode: str
    columns: tuple[str, ...]
    choices: dict[str, list[str]]
    refusals: dict[str, str]
    cohort_industry: str = ""
    cohort_region: str = ""
    cohort_name: str = ""

    # ── Predicates the three consumers ask ──────────────────────────────────
    @property
    def is_single_bu(self) -> bool:
        return self.mode == SINGLE_BU

    @property
    def per_player_scope(self) -> bool:
        """True when a row decides its own company, i.e. when industry/region
        carry information rather than being cohort-wide constants."""
        return INDUSTRY in self.columns

    def refusal_for(self, column: str) -> str | None:
        tpl = self.refusals.get(column)
        return tpl.format(col=column) if tpl else None

    def allows(self, column: str) -> bool:
        return column in self.columns

    # ── Defaults: a blank scope cell inherits the cohort's own formation value
    def default_for(self, column: str) -> str:
        if column == INDUSTRY:
            return self.cohort_industry
        if column == REGION:
            return self.cohort_region
        return ""

    # ── Template material ───────────────────────────────────────────────────
    def example_rows(self) -> list[list[str]]:
        """Two example rows, valid under THIS shape — a template that fails its
        own parser is worse than no template. The second row leaves the optional
        fields blank so the author can see that blank is legal."""
        base = [
            ["Priya Raman", "priya@example.edu", "MBA 2026"],
            ["Sam Okoye", "sam@example.edu", ""],
        ]
        if not self.per_player_scope:
            return base
        verticals = self.choices.get(INDUSTRY, [])
        regions = self.choices.get(REGION, [])
        first_v = self.cohort_industry or (verticals[0] if verticals else "")
        # A DIFFERENT vertical on the second row, because the whole point of
        # this shape is that two players may run different companies. Falls back
        # to the first when the catalogue somehow has only one entry.
        second_v = next((v for v in verticals if v != first_v), first_v)
        first_r = self.cohort_region if self.cohort_region in regions else (regions[0] if regions else "")
        second_r = next((r for r in regions if r != first_r), first_r)
        return [base[0] + [first_v, first_r], base[1] + [second_v, second_r]]

    def help_lines(self) -> list[str]:
        """The 'How to use' sheet. Written from the shape so it can never
        describe a column this template does not ship."""
        out = [
            f"Roster for: {self.cohort_name or 'this cohort'}",
            f"Simulation mode: {self.mode_label()}",
            "",
            "Fill one row per player on the 'Players' sheet.",
            "'name' is required. Everything else is optional.",
            "'email' is optional but must look like an email if present.",
            "'programme' is optional — an open-enrolment cohort has none.",
            "",
        ]
        if self.per_player_scope:
            out += [
                "EACH PLAYER RUNS THEIR OWN COMPANY.",
                "  industry_vertical — the business this player runs.",
                "  region_id         — the market they run it in.",
                "Pick both from the dropdowns; free text is rejected.",
                "Leave either blank to inherit the cohort's own setting "
                f"({self.cohort_industry or '—'} / {self.cohort_region or '—'}).",
                "Two players may run different industries in different regions —",
                "that is what this mode is for.",
                "",
                "You do NOT set a business-unit slot. It is derived from the",
                "industry you pick, so the two can never disagree.",
                "",
                "industry_vertical values: " + ", ".join(self.choices.get(INDUSTRY, [])),
                "region_id values: " + ", ".join(self.choices.get(REGION, [])),
            ]
        else:
            out += [
                "EVERY PLAYER RUNS THE WHOLE GROUP — all four business units.",
                "No player is assigned a company, so this sheet has no",
                "assigned_bu, industry_vertical or region_id column.",
                "",
                "The cohort's four verticals and its region(s) are set once, for",
                "everyone, in Edit Cohort. Adding a per-player business unit here",
                "would scope that player down to a single business — silently, and",
                "that is the Single Business mode, not this one. So such a column",
                "is refused on upload rather than half-honoured.",
            ]
        out += [
            "",
            f"Maximum {_ceiling()} players per cohort.",
            "A single bad row aborts the whole upload — nothing is created.",
            "Each player gets a random temporary password, shown in the Player Registry.",
        ]
        return out

    def mode_label(self) -> str:
        return "Single Business (one company per player)" if self.is_single_bu \
            else "4-BU Conglomerate (every player runs all four)"

    # ── API projection for the upload modal ─────────────────────────────────
    def as_api(self) -> dict:
        return {
            "mode": self.mode,
            "mode_label": self.mode_label(),
            "per_player_scope": self.per_player_scope,
            "columns": list(self.columns),
            "required": [NAME],
            "choices": {k: list(v) for k, v in self.choices.items()},
            "cohort": {
                "cohort_name": self.cohort_name,
                "industry_vertical": self.cohort_industry,
                "region_id": self.cohort_region,
            },
            "refused_columns": {c: self.refusal_for(c) for c in self.refusals},
        }


# ── Vocabularies (delegated, never retyped) ─────────────────────────────────

def _ceiling() -> int:
    try:
        from player_capacity import MAX_PLAYERS_CEILING
        return MAX_PLAYERS_CEILING
    except Exception:
        return 20


def _slot_map() -> dict[str, str]:
    """vertical id -> owning seed slot, for every industry a cohort can be
    formed with.

    Derived from bu_profiles.SLOT_FIT_MAP + DEFAULT_SLOTS, deliberately NOT from
    router.VERTICAL_SLOT_MAP even though router is where join_session reads it.
    The two are equal by construction (asserted by a tripwire test), but
    importing `router` here would drag in `database` and therefore asyncpg, and
    every resolver in this file is fail-open — so on any host where that import
    is unavailable the vocabulary would silently collapse to the four default
    slots and the dropdown would start refusing the very vertical the cohort was
    formed with. A fail-open catalogue must have a dependency-light source or it
    is not a catalogue, it is a coin flip. bu_profiles is that source: it is what
    create_session itself resolves slots through.
    """
    try:
        from bu_profiles import SLOT_FIT_MAP, DEFAULT_SLOTS
        out: dict[str, str] = {}
        for slot in DEFAULT_SLOTS:
            out[slot] = slot                       # the slot's own native vertical
            for v in SLOT_FIT_MAP.get(slot, []):   # substitutes that fit the slot
                out[v] = slot
        if out:
            return out
    except Exception:
        pass
    return {s: s for s in ("pharma", "electronics", "consumer_goods", "software")}


def formation_verticals() -> list[str]:
    """Every industry a cohort can be formed with, in slot order.

    Slot order rather than alphabetical, so related industries sit together in
    the dropdown exactly as the Create-Cohort picker groups them, with each
    slot's native vertical first.
    """
    slot_map = _slot_map()
    try:
        from bu_profiles import DEFAULT_SLOTS
        order = {slot: i for i, slot in enumerate(DEFAULT_SLOTS)}
    except Exception:
        order = {}
    return [
        v for v, _s in sorted(
            slot_map.items(),
            # (slot position, native-before-substitute, name) — total and stable
            key=lambda kv: (order.get(kv[1], 99), kv[0] != kv[1], kv[0]),
        )
    ]


def formation_regions() -> list[str]:
    try:
        import excel_dropdowns as xd
        out = list(xd.region_ids())
        if out:
            return out
    except Exception:
        pass
    return ["asean", "south_asia", "china", "europe", "north_america", "africa"]


def vertical_slot(vertical_id: str) -> str:
    """The seed slot that owns a vertical — the value that belongs in
    `assigned_bu`. Same resolution router/join performs, so a roster and a join
    can never disagree about which BU a player is in. An unknown id is returned
    unchanged: create_session has its own legacy path for a raw vertical id and
    is a better place to guess than this one."""
    vid = (vertical_id or "").strip()
    if not vid:
        return ""
    return _slot_map().get(vid, vid)


# ── The resolver ────────────────────────────────────────────────────────────

def resolve_roster_shape(session_info: dict | None) -> RosterShape:
    """The roster shape for a cohort, from its formation data.

    A missing / unreadable session resolves to the CONGLOMERATE shape, which is
    both the system default (`simulation_mode` defaults to "conglomerate") and
    the safe one: it refuses the scope columns instead of accepting values it
    cannot validate against a cohort it could not read.
    """
    info = session_info or {}
    mode = normalise_mode(info.get("simulation_mode"))
    industry = str(info.get("industry_vertical") or "").strip()
    region = str(info.get("region_id") or "").strip()
    name = str(info.get("cohort_name") or "").strip()

    if mode == SINGLE_BU:
        return RosterShape(
            mode=SINGLE_BU,
            columns=_IDENTITY_COLUMNS + _SCOPE_COLUMNS,
            choices={
                INDUSTRY: formation_verticals(),
                REGION: formation_regions(),
            },
            refusals=dict(_REFUSAL_SINGLE_BU),
            cohort_industry=industry,
            cohort_region=region,
            cohort_name=name,
        )

    return RosterShape(
        mode=CONGLOMERATE,
        columns=_IDENTITY_COLUMNS,
        choices={},
        refusals=dict(_REFUSAL_CONGLOMERATE),
        cohort_industry=industry,
        # A conglomerate cohort's region is cohort-wide (or per-BU when
        # multi_region). Carried for display only — it is not a row default,
        # because there is no row column to default.
        cohort_region=region,
        cohort_name=name,
    )


def shape_from_cohort_row(row: dict | None) -> RosterShape:
    """Shape for a cohort that does not exist yet — a row on the master
    provisioning workbook's Cohorts sheet. Same resolver, so the Players sheet
    of a master workbook is held to exactly the contract the cohort it
    provisions will enforce once it exists."""
    r = row or {}
    return resolve_roster_shape({
        "simulation_mode": r.get("simulation_mode"),
        "industry_vertical": r.get("industry_vertical"),
        "region_id": r.get("region_id"),
        "cohort_name": r.get("cohort_name") or r.get("ref") or "",
    })
