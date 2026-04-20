import re
import os

path = r"backend\round_logic.py"
if os.path.exists(path):
    with open(path, "r", encoding="utf-8") as f:
        content = f.read()

    content = re.sub(r'_SDG_BU_IDS = \{"sub_saharan_corridor", "south_asia_subcontinent", "southeast_asia_hub",\s*"latin_america_basin", "northern_transition_zone"\}\n', '', content)
    content = re.sub(r'    if any\(b\["bu_id"\] in _SDG_BU_IDS for b in bus\):\n        return get_sdg_round_options\(round_number\)\n', '', content)
    
    # Strip terminal valuation sdg section
    content = re.sub(r'\s*is_sdg = any\(b\["bu_id"\] in _SDG_BU_IDS for b in bus\)', '', content)
    content = re.sub(r'    if is_sdg:.*?elif is_healthcare:', '    if is_healthcare:', content, flags=re.DOTALL)
    
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)

print("Round logic terminal section cleaned")
