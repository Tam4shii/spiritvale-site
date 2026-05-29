#!/usr/bin/env python3
"""Build search-index.json by flattening all versioned patch files into bullet-level entries."""
import json, glob, os, re, sys
from datetime import datetime, timezone

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
PATCHES_DIR = os.path.join(ROOT, 'patches')
OUTPUT = os.path.join(ROOT, 'search-index.json')

# Canonical entity tags — order matters (longer phrases first to avoid partial matches)
TAG_RULES = [
    ('Echoing Spire', 'echoing-spire'),
    ('Forgotten Depths', 'forgotten-depths'),
    ('Necromancer', 'necromancer'),
    ('Berserker', 'berserker'),
    ('Shinobi', 'shinobi'),
    ('Paladin', 'paladin'),
    ('Mage', 'mage'),
    ('Arena', 'arena'),
    ('Crafting', 'crafting'),
    ('Guild', 'guild'),
    ('Boss', 'boss'),
    ('PvP', 'pvp'),
]
_TAG_PATTERNS = [(re.compile(r'\b' + re.escape(kw) + r'\b', re.IGNORECASE), slug) for kw, slug in TAG_RULES]

def extract_tags(text: str) -> list:
    seen = set()
    return [slug for _, slug in _TAG_PATTERNS
            if _.search(text) and not seen.add(slug)]

entries = []
patch_files = sorted(glob.glob(os.path.join(PATCHES_DIR, 'v*.json')))
for path in patch_files:
    with open(path) as f:
        p = json.load(f)
    version = p['version']
    patch_title = p.get('title', f'v{version}')
    date = p.get('date', '')
    for change_type in ('added', 'changed', 'deprecated', 'removed', 'fixed', 'security'):
        for i, text in enumerate(p.get(change_type) or []):
            entries.append({
                'id': f'v{version}-{change_type}-{i}',
                'version': version,
                'patch_title': patch_title,
                'date': date,
                'type': change_type,
                'text': text,
                'tags': extract_tags(text),
                'url': f'/patch/?v={version}'
            })

output = {
    'generated_at': datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ'),
    'total': len(entries),
    'patch_count': len(patch_files),
    'entries': entries
}
with open(OUTPUT, 'w') as f:
    json.dump(output, f, separators=(',', ':'))
print(f'search-index.json: {len(entries)} entries from {len(patch_files)} patches', file=sys.stderr)
