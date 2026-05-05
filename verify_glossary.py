import sys
sys.path.insert(0, 'backend')
from admin_analytics import _glossary_terms

print(f"Backend glossary: {len(_glossary_terms)} terms")
refs = [t for t in _glossary_terms if t.get('weblink')]
print(f"Terms with references: {len(refs)}")
print()
print("=== Terms with Academic References ===")
for t in refs:
    print(f"  {t['term']}: {t['weblink'][:80]}")
print()
# Count unique tags
all_tags = set()
for t in _glossary_terms:
    all_tags.update(t.get('tags', []))
print(f"Total unique tags: {len(all_tags)}")
print(f"Tags: {sorted(all_tags)}")
