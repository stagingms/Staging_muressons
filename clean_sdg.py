import os, re

def replace_in_file(filepath, replacements):
    if not os.path.exists(filepath): return
    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()
    for old, new in replacements:
        content = content.replace(old, new)
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(content)

# database_memory.py
replace_in_file(r"backend\database_memory.py", [
    ('elif industry == "un_sdg":\n        filename = "seed_sdg.json"\n    ', ""),
    ('_PARADIGM_INDUSTRY_MAP = {"healthcare": "healthcare", "un_sdg": "un_sdg"}', '_PARADIGM_INDUSTRY_MAP = {"healthcare": "healthcare"}')
])

# router.py
replace_in_file(r"backend\router.py", [
    ('_VALID_PARADIGMS = {"legacy_abc", "multi_toggles", "advanced_climate", "healthcare", "un_sdg"}', '_VALID_PARADIGMS = {"legacy_abc", "multi_toggles", "advanced_climate", "healthcare"}'),
    ('        elif body.decision_paradigm == "un_sdg":\n            seed = _load_seed(industry="un_sdg")\n', ''),
    ('                elif body.decision_paradigm == "un_sdg":\n                    from sdg_configs import SDG_CRISES\n                    crises = SDG_CRISES\n', ''),
    (', "un_sdg"', ''),
    ("Must be 'legacy_abc', 'multi_toggles', 'advanced_climate', 'healthcare', or 'un_sdg'.", "Must be 'legacy_abc', 'multi_toggles', 'advanced_climate', or 'healthcare'."),
])

# models.py
replace_in_file(r"backend\models.py", [
    ('    un_sdg = "un_sdg"\n', '')
])

# admin_router.py
replace_in_file(r"backend\admin_router.py", [
    ('raw_overrides = {"legacy_abc": {}, "multi_toggles": {}, "healthcare": {}, "un_sdg": {}}', 'raw_overrides = {"legacy_abc": {}, "multi_toggles": {}, "healthcare": {}}'),
    ('paradigm in ["legacy_abc", "healthcare", "un_sdg"]', 'paradigm in ["legacy_abc", "healthcare"]')
])

# audit_api.py
replace_in_file(r"backend\audit_api.py", [
    (', "un_sdg"', '')
])

# engine.py
if os.path.exists(r"backend\engine.py"):
    with open(r"backend\engine.py", "r", encoding="utf-8") as f:
        content = f.read()
    content = re.sub(r' +if decision_paradigm == "un_sdg":.*?return next_global, next_bus\n', '', content, flags=re.DOTALL)
    content = re.sub(r' *if decision_paradigm != "un_sdg" else global_emissions,', ',', content) 
    with open(r"backend\engine.py", "w", encoding="utf-8") as f:
        f.write(content)

print("Backend un_sdg refs cleaned")
