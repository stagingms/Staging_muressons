import asyncio
from router import pre_tick
from round_logic import pre_tick
import datetime

gs = {"round_number": 2, "corporate_treasury": 100000000}
bus = [
    {"bu_id": "hospitals", "revenue_base": 100},
    {"bu_id": "clinics", "revenue_base": 100},
    {"bu_id": "telehealth", "revenue_base": 100}
]

decs = [
    {"bu_id": "hospitals", "capex_allocated": 1000, "decision_node_id": "round_2_hospitals"},
    {"bu_id": "clinics", "capex_allocated": 1000, "decision_node_id": "round_2_clinics"},
    {"bu_id": "telehealth", "capex_allocated": 1000, "decision_node_id": "round_2_telehealth"}
]

result = pre_tick(2, gs, bus, decs, 0, force_override_cfo=False)
print(result)

