import re
import os

path = r"backend\round_logic.py"
if os.path.exists(path):
    with open(path, "r", encoding="utf-8") as f:
        content = f.read()

    content = re.sub(r"from sdg_configs import .*?\n", "", content)
    content = re.sub(r' +elif decision_paradigm == "un_sdg":.*?return \[\].*?\n', '', content, flags=re.DOTALL)
    content = re.sub(r' +if decision_paradigm == "un_sdg":.*?return next_global, next_bus\n', '', content, flags=re.DOTALL)
    content = re.sub(r' *if decision_paradigm != "un_sdg" else global_emissions,', ',', content)
    
    # We must also clean up the test_fallback error but that was "import asyncpg" missing. I will leave that.
    
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)

print("Round logic cleaned")
