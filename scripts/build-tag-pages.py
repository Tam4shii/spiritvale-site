#!/usr/bin/env python3
"""Generate static /tag/<slug>/index.html + feed.xml pages + /tag/index.json from search-index.json."""
import json, os, re, sys
from collections import defaultdict

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
INDEX = os.path.join(ROOT, 'search-index.json')
TAG_DIR = os.path.join(ROOT, 'tag')

BADGE = {
    'added': ('<span style="color:#86efac">added</span>', '#86efac'),
    'changed': ('<span style="color:#fcd34d">changed</span>', '#fcd34d'),
    'fixed': ('<span style="color:#93c5fd">fixed</span>', '#93c5fd'),
    'removed': ('<span style="color:#fca5a5">removed</span>', '#fca5a5'),
    'deprecated': ('<span style="color:#fb923c">deprecated</span>', '#fb923c'),
    'security': ('<span style="color:#f472b6">security</span>', '#f472b6'),
}

DISPLAY_NAME = {
    'paladin': 'Paladin',
    'shinobi': 'Shinobi',
    'berserker': 'Berserker',
    'necromancer': 'Necromancer',
    'mage': 'Mage',
    'echoing-spire': 'Echoing Spire',
    'forgotten-depths': 'Forgotten Depths',
    'arena': 'Arena',
    'boss': 'Boss',
    'crafting': 'Crafting',
    'guild': 'Guild',
    'pvp': 'PvP',
}

# TODO(class-pages): use to generate /class/<slug>/ pages with lore header + cross-version skill delta
CLASS_TAGS = {'shinobi', 'berserker', 'necromancer', 'paladin', 'mage'}

CSS = """
  :root{--bg:#0a0612;--fg:#e8e3f0;--muted:#8b82a0;--accent:#a78bfa;--accent-2:#7c3aed;--card:rgba(167,139,250,.08);--border:rgba(167,139,250,.2)}
  *{box-sizing:border-box;margin:0;padding:0}
  body{font-family:-apple-system,BlinkMacSystemFont,"Inter",sans-serif;background:var(--bg);color:var(--fg);line-height:1.6;min-height:100vh;padding:2rem;
    background-image:radial-gradient(at 20% 30%,rgba(124,58,237,.15),transparent 50%),radial-gradient(at 80% 80%,rgba(167,139,250,.08),transparent 50%)}
  a{color:var(--accent);text-decoration:none}a:hover{text-decoration:underline}
  header{max-width:860px;margin:0 auto 2rem}
  .breadcrumb{font-size:.8rem;color:var(--muted);margin-bottom:.5rem}
  h1{font-size:1.8rem;font-weight:700;color:var(--accent);margin-bottom:.25rem}
  .subtitle{color:var(--muted);font-size:.95rem}
  .entries{max-width:860px;margin:0 auto;display:flex;flex-direction:column;gap:.75rem}
  .entry{background:var(--card);border:1px solid var(--border);border-radius:8px;padding:.9rem 1rem}
  .entry-meta{font-size:.75rem;color:var(--muted);margin-bottom:.3rem}
  .entry-text{font-size:.95rem}
  .tag-chip{display:inline-block;font-size:.7rem;padding:.1rem .45rem;border-radius:4px;margin-right:.3rem;margin-top:.35rem;background:rgba(167,139,250,.15);border:1px solid var(--border);color:var(--muted)}
  .tag-index{max-width:860px;margin:2rem auto 0;display:flex;flex-wrap:wrap;gap:.5rem}
  footer{max-width:860px;margin:3rem auto 0;font-size:.8rem;color:var(--muted);text-align:center}
"""

def page_html(slug, entries):
    name = DISPLAY_NAME.get(slug, slug.replace('-', ' ').title())
    rows = []
    for e in entries:
        badge_html, _ = BADGE.get(e['type'], (e['type'], '#888'))
        other_tags = ''.join(f'<a class="tag-chip" href="/tag/{t}/">{DISPLAY_NAME.get(t,t)}</a>'
                             for t in e.get('tags', []) if t != slug)
        rows.append(f"""
    <div class="entry">
      <div class="entry-meta">{badge_html} &middot; <a href="{e['url']}">{e['patch_title']}</a> ({e['date']})</div>
      <div class="entry-text">{e['text']}</div>
      {other_tags}
    </div>""")
    body = '\n'.join(rows)
    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>SpiritVale — {name} changes</title>
<meta name="description" content="All SpiritVale patch changes tagged {name} across every version.">
<meta property="og:type" content="website">
<meta property="og:title" content="SpiritVale — {name} changes">
<meta property="og:description" content="All SpiritVale patch changes tagged {name} across {len(entries)} entries.">
<meta property="og:url" content="https://spiritvale.tama.sh/tag/{slug}/">
<meta property="og:image" content="https://spiritvale.tama.sh/og/latest.png">
<link rel="icon" type="image/svg+xml" href="/favicon.svg">
<link rel="canonical" href="https://spiritvale.tama.sh/tag/{slug}/">
<link rel="alternate" type="application/atom+xml" title="SpiritVale — {name} Changes" href="/tag/{slug}/feed.xml">
<style>{CSS}</style>
</head>
<body>
<header>
  <div class="breadcrumb"><a href="/">SpiritVale</a> › <a href="/tag/">Tags</a> › {name}</div>
  <h1>{name}</h1>
  <p class="subtitle">{len(entries)} change{'s' if len(entries)!=1 else ''} across all patches</p>
</header>
<div class="entries">{body}
</div>
<footer>
  <a href="/">Home</a> &middot; <a href="/search/">Search</a> &middot; <a href="/tag/">All Tags</a>
</footer>
</body>
</html>"""

def tag_index_html(tag_counts):
    chips = ''.join(
        f'<a href="/tag/{slug}/" style="display:inline-flex;align-items:center;gap:.4rem;padding:.4rem .85rem;background:var(--card);border:1px solid var(--border);border-radius:6px;color:var(--accent)">'
        f'{DISPLAY_NAME.get(slug,slug)} <span style="color:var(--muted);font-size:.8rem">({count})</span></a>'
        for slug, count in sorted(tag_counts.items(), key=lambda x: -x[1])
    )
    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>SpiritVale — Tags</title>
<meta name="description" content="Browse SpiritVale patch notes by class, system, or area tag.">
<link rel="icon" type="image/svg+xml" href="/favicon.svg">
<link rel="canonical" href="https://spiritvale.tama.sh/tag/">
<style>{CSS}</style>
</head>
<body>
<header>
  <div class="breadcrumb"><a href="/">SpiritVale</a> › Tags</div>
  <h1>Tags</h1>
  <p class="subtitle">Browse patch changes by class, system, or area</p>
</header>
<div class="tag-index">{chips}</div>
<footer>
  <a href="/">Home</a> &middot; <a href="/search/">Search</a>
</footer>
</body>
</html>"""

def _esc(s):
    return s.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;').replace('"', '&quot;')

def tag_feed_xml(slug, entries):
    name = DISPLAY_NAME.get(slug, slug.replace('-', ' ').title())
    by_version = {}
    for e in entries:
        v = e['version']
        if v not in by_version:
            by_version[v] = {'date': e['date'], 'patch_title': e['patch_title'], 'items': []}
        by_version[v]['items'].append(e)
    sorted_v = sorted(by_version.items(), key=lambda x: x[1]['date'], reverse=True)
    updated = (sorted_v[0][1]['date'] if sorted_v else '2026-01-01') + 'T00:00:00Z'
    entries_xml = []
    for version, vd in sorted_v:
        items = vd['items']
        summary = '; '.join(_esc(i['text']) for i in items[:5])
        if len(items) > 5:
            summary += f' … ({len(items) - 5} more)'
        patch_title = vd['patch_title']
        display = f'v{version}' + (f' – {_esc(patch_title)}' if patch_title else '')
        entries_xml.append(f"""  <entry>
    <id>https://spiritvale.tama.sh/patches/v{version}.json#tag-{slug}</id>
    <title>{display} [{_esc(name)}]</title>
    <link rel="alternate" href="https://spiritvale.tama.sh/patch/?v={version}" />
    <updated>{vd['date']}T00:00:00Z</updated>
    <summary type="text">{summary}</summary>
  </entry>""")
    return f"""<?xml version="1.0" encoding="UTF-8"?>
<feed xmlns="http://www.w3.org/2005/Atom">
  <id>https://spiritvale.tama.sh/tag/{slug}/feed.xml</id>
  <title>SpiritVale — {_esc(name)} Changes</title>
  <link rel="alternate" type="text/html" href="https://spiritvale.tama.sh/tag/{slug}/" />
  <link rel="self" type="application/atom+xml" href="https://spiritvale.tama.sh/tag/{slug}/feed.xml" />
  <updated>{updated}</updated>
  <author><name>SpiritVale Community Archive</name></author>

{"".join(chr(10) + e for e in entries_xml)}
</feed>"""


with open(INDEX) as f:
    data = json.load(f)

by_tag = defaultdict(list)
for e in data['entries']:
    for tag in e.get('tags', []):
        by_tag[tag].append(e)

os.makedirs(TAG_DIR, exist_ok=True)

for slug, entries in by_tag.items():
    slug_dir = os.path.join(TAG_DIR, slug)
    os.makedirs(slug_dir, exist_ok=True)
    with open(os.path.join(slug_dir, 'index.html'), 'w') as f:
        f.write(page_html(slug, entries))
    with open(os.path.join(slug_dir, 'feed.xml'), 'w') as f:
        f.write(tag_feed_xml(slug, entries))

with open(os.path.join(TAG_DIR, 'index.html'), 'w') as f:
    f.write(tag_index_html({slug: len(entries) for slug, entries in by_tag.items()}))

tag_json = {
    'generated_at': data['generated_at'],
    'tags': {slug: {'count': len(entries), 'url': f'/tag/{slug}/'} for slug, entries in sorted(by_tag.items(), key=lambda x: -len(x[1]))}
}
with open(os.path.join(TAG_DIR, 'index.json'), 'w') as f:
    json.dump(tag_json, f, separators=(',', ':'))

print(f'tag pages: {len(by_tag)} tags, {sum(len(v) for v in by_tag.values())} total tagged entries', file=sys.stderr)
