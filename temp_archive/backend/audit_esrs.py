src = open('materiality_db.py', encoding='utf-8').read()
lines = src.splitlines()
missing = []
for i, l in enumerate(lines):
    stripped = l.strip()
    if '"id":' in stripped and '"esrs_topic"' not in stripped and 'mitigation_cost_usd' in stripped:
        missing.append(f'{i+1}: {stripped[:90]}')
print(f'{len(missing)} issues missing esrs_topic:')
for m in missing:
    print(m)
