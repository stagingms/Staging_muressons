import os
import re

backend_file = 'c:/Users/Home/.gemini/antigravity/scratch/muressons-sim/backend/admin_router.py'
with open(backend_file, 'r', encoding='utf-8') as f:
    content = f.read()

# Add the dependency
dep_code = '''
from fastapi import Header, Depends

def get_fac_role(x_facilitator_id: str = Header(None)):
    if not x_facilitator_id:
        return 'facilitator'
    fac = next((f for f in _facilitator_registry if f['facilitator_id'] == x_facilitator_id), None)
    return get_role(fac) if fac else 'facilitator'

def require_super_admin(role: str = Depends(get_fac_role)):
    if role != 'super_admin':
        raise HTTPException(status_code=403, detail='Super Admin required')
'''

if 'def get_fac_role' not in content:
    content = content.replace('from pydantic import BaseModel', 'from pydantic import BaseModel' + dep_code)

# Add Depends to endpoints
endpoints_to_protect = [
    r'(@admin_router\.patch\(\"/global-settings\".*?\nasync def patch_global_settings\(body: GlobalSettingsPatch)',
    r'(@admin_router\.put\(\"/facilitators/\{fac_id\}/role\".*?\nasync def update_facilitator_role\(fac_id: str, body: dict = Body\(\.\.\.\))',
    r'(@admin_router\.post\(\"/archetypes\".*?\nasync def add_archetype\(body: dict = Body\(\.\.\.\))',
    r'(@admin_router\.put\(\"/archetypes/\{key\}\".*?\nasync def update_archetype\(key: str, body: dict = Body\(\.\.\.\))',
    r'(@admin_router\.delete\(\"/archetypes/\{key\}\".*?\nasync def delete_archetype\(key: str)',
    r'(@admin_router\.delete\(\"/reset-all\".*?\nasync def reset_all_sessions\()',
]

for pattern in endpoints_to_protect:
    content = re.sub(pattern, r'\1, _guard: None = Depends(require_super_admin)', content)

with open(backend_file, 'w', encoding='utf-8') as f:
    f.write(content)
print('Backend patched')
