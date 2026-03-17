"""
Muressons Global Command — Round 2 Data Dictionary
20 CSRD Materiality Issues configured for the Double Materiality Matrix
"""

CSRD_ISSUES = {
    # ── Quadrant 1 (High Fin/High Impact - The Target) ───────────
    "water_scarcity": {
        "id": "water_scarcity",
        "title": "Water Scarcity in Deccan Plateau",
        "hover_description": "Hits Pharma ops; destroys local ag",
        "correct_quadrant": 1,
    },
    "e_waste": {
        "id": "e_waste",
        "title": "E-Waste & Toxic Mineral Runoff",
        "hover_description": "Future EU bans; massive eco damage",
        "correct_quadrant": 1,
    },
    "tier3_labor": {
        "id": "tier3_labor",
        "title": "Tier-3 Supply Chain Labor Practices",
        "hover_description": "Boycott risk; severe human rights",
        "correct_quadrant": 1,
    },
    "ai_bias": {
        "id": "ai_bias",
        "title": "AI Algorithmic Bias & Redlining",
        "hover_description": "Massive fines; systemic inequality",
        "correct_quadrant": 1,
    },
    "scope3_carbon": {
        "id": "scope3_carbon",
        "title": "Scope 3 Carbon Emissions",
        "hover_description": "Impending carbon tax; global warming",
        "correct_quadrant": 1,
    },
    "plastic_packaging": {
        "id": "plastic_packaging",
        "title": "End-of-Life Plastic Packaging",
        "hover_description": "15% EPR tax; ocean microplastics",
        "correct_quadrant": 1,
    },

    # ── Quadrant 2 (Low Fin/High Impact) ─────────────────────────
    "employee_volunteering": {
        "id": "employee_volunteering",
        "title": "Generic Employee Volunteering",
        "hover_description": "Low Fin/High Impact",
        "correct_quadrant": 2,
    },
    "philanthropy": {
        "id": "philanthropy",
        "title": "Corporate Philanthropy & Local Schools",
        "hover_description": "Low Fin/High Impact",
        "correct_quadrant": 2,
    },
    "open_source_ai": {
        "id": "open_source_ai",
        "title": "Open-Sourcing Proprietary AI for NGOs",
        "hover_description": "Low Fin/High Impact",
        "correct_quadrant": 2,
    },
    "living_wage": {
        "id": "living_wage",
        "title": "Living Wage Standardization across Tier-4",
        "hover_description": "Low Fin/High Impact",
        "correct_quadrant": 2,
    },

    # ── Quadrant 3 (High Fin/Low Impact) ─────────────────────────
    "semi_prices": {
        "id": "semi_prices",
        "title": "Raw Semiconductor Price Volatility",
        "hover_description": "High Fin/Low Impact",
        "correct_quadrant": 3,
    },
    "software_competitor": {
        "id": "software_competitor",
        "title": "Consumer Shift to Competitor Software",
        "hover_description": "High Fin/Low Impact",
        "correct_quadrant": 3,
    },
    "currency_exchange": {
        "id": "currency_exchange",
        "title": "Currency Exchange Rate Fluctuations",
        "hover_description": "High Fin/Low Impact",
        "correct_quadrant": 3,
    },
    "eu_tax": {
        "id": "eu_tax",
        "title": "Corporate Tax Rate Changes in EU",
        "hover_description": "High Fin/Low Impact",
        "correct_quadrant": 3,
    },

    # ── Quadrant 4 (Low Fin/Low Impact) ──────────────────────────
    "paper_recycling": {
        "id": "paper_recycling",
        "title": "Office Paper Recycling at HQ",
        "hover_description": "Low Fin/Low Impact",
        "correct_quadrant": 4,
    },
    "plastic_straws": {
        "id": "plastic_straws",
        "title": "Replacing Plastic Straws in Cafeteria",
        "hover_description": "Low Fin/Low Impact",
        "correct_quadrant": 4,
    },
    "exec_travel": {
        "id": "exec_travel",
        "title": "Executive Travel Carbon Offsets",
        "hover_description": "Low Fin/Low Impact",
        "correct_quadrant": 4,
    },
    "earth_day": {
        "id": "earth_day",
        "title": "Annual Earth Day Social Media Campaign",
        "hover_description": "Low Fin/Low Impact",
        "correct_quadrant": 4,
    },
    "ergonomic_chairs": {
        "id": "ergonomic_chairs",
        "title": "Ergonomic Chairs for Developers",
        "hover_description": "Low Fin/Low Impact",
        "correct_quadrant": 4,
    },
    "led_bulbs": {
        "id": "led_bulbs",
        "title": "LED Bulb Swaps in Admin Offices",
        "hover_description": "Low Fin/Low Impact",
        "correct_quadrant": 4,
    },
}

ROUND_2_DEFAULT_CONFIG = {
    "round_2_config": {
        "total_materiality_budget": 15000000,
        "consultant_feature": {
            "enabled": True,
            "consultant_fee_usd": 1500000,
            "auto_solve_count": 5
        }
    }
}
