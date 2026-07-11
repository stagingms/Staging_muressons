import os
import ast

files = [
    "biodiversity_engine.py", "balance_sheet.py", "meadows_leverage.py",
    "board_governance.py", "org_politics.py", "tcfd_scenarios.py",
    "regulatory_sandbox.py", "market_dynamics.py", "npc_stakeholders.py",
    "dynamic_cases.py", "branching_engine.py", "supply_chain_network.py"
]

base_path = r"c:\Users\Home\.gemini\antigravity\scratch\muressons-sim\backend"

with open(os.path.join(base_path, "extracted_docs.md"), "w", encoding="utf-8") as out:
    for f in files:
        path = os.path.join(base_path, f)
        if os.path.exists(path):
            with open(path, "r", encoding="utf-8", errors="ignore") as py_file:
                content = py_file.read()
            try:
                module = ast.parse(content)
                docstring = ast.get_docstring(module)
                out.write(f"=== {f} ===\n")
                if docstring:
                    out.write(docstring + "\n")
                out.write("-" * 40 + "\n")
            except Exception as e:
                out.write(f"Error parsing {f}: {e}\n")
