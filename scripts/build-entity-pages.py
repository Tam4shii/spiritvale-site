#!/usr/bin/env python3
"""Generate per-entity timeline pages at /entity/<slug>/index.html.

poedb.tw pattern: per-entity balance history pivoted around game entities, not dates.
Entities are found by text-keyword matching AND tag presence — capturing mentions
that aren't explicitly tagged (e.g. "Shinobi Fan of Knives" in a pvp-tagged entry).

Outputs:
  entity/<slug>/index.html  — timeline grouped by patch version
  entity/index.html         — entity index listing
  entity/index.json         — machine-readable entity manifest
"""
import json
import os
import re
from collections import defaultdict

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
INDEX_PATH = os.path.join(ROOT, "search-index.json")
ENTITY_DIR = os.path.join(ROOT, "entity")

# Entity definitions: slug → display_name, one-line description, keyword pattern, tag aliases.
# Pattern matches text field; tags matches the entry's tags list.
# Using both ensures we catch un-tagged mentions (the key value-add over tag pages).
ENTITIES = {
    "shinobi": {
        "name": "Shinobi",
        "desc": "Agility assassin specialising in clones, kunais, and burst combos.",
        "pattern": re.compile(r"\bshinobi\b", re.IGNORECASE),
        "tags": {"shinobi"},
    },
    "paladin": {
        "name": "Paladin",
        "desc": "Holy warrior with melee burst and support skills.",
        "pattern": re.compile(r"\bpaladin\b", re.IGNORECASE),
        "tags": {"paladin"},
    },
    "berserker": {
        "name": "Berserker",
        "desc": "Rage-fuelled brawler with high burst and self-sustain via Siphon.",
        "pattern": re.compile(r"\bberserker\b", re.IGNORECASE),
        "tags": {"berserker"},
    },
    "necromancer": {
        "name": "Necromancer",
        "desc": "Summoner that reanimates enemies and commands undead minions.",
        "pattern": re.compile(r"\bnecromancer\b", re.IGNORECASE),
        "tags": {"necromancer"},
    },
    "echoing-spire": {
        "name": "Echoing Spire",
        "desc": "100-floor endgame dungeon requiring a Spire Key. Rewards Umbral Fragments.",
        "pattern": re.compile(r"\bechoing[\s\-]spire\b|\bspire key\b|\bumbral\b", re.IGNORECASE),
        "tags": {"echoing-spire"},
    },
    "forgotten-depths": {
        "name": "Forgotten Depths",
        "desc": "Mid-game underground dungeon zone with Crafter NPCs.",
        "pattern": re.compile(r"\bforgotten[\s\-]depths?\b", re.IGNORECASE),
        "tags": {"forgotten-depths"},
    },
    "arena": {
        "name": "Arena",
        "desc": "Instanced 2v2 and 3v3 PvP modes with MMR and leaderboard rewards.",
        "pattern": re.compile(r"\barena\b", re.IGNORECASE),
        "tags": {"arena"},
    },
    "boss": {
        "name": "Bosses",
        "desc": "World bosses with KS protection, regen mechanics, and exclusive drops.",
        "pattern": re.compile(r"\bboss(?:es)?\b", re.IGNORECASE),
        "tags": {"boss"},
    },
}

BADGE = {
    "added": ('<span style="color:#86efac">added</span>', "#86efac"),
    "changed": ('<span style="color:#fcd34d">changed</span>', "#fcd34d"),
    "fixed": ('<span style="color:#93c5fd">fixed</span>', "#93c5fd"),
    "removed": ('<span style="color:#fca5a5">removed</span>', "#fca5a5"),
}

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
  .desc{margin-top:.6rem;color:var(--fg);font-size:.95rem;opacity:.85}
  .section{max-width:860px;margin:1.5rem auto 0}
  .section-head{display:flex;align-items:baseline;gap:.75rem;margin-bottom:.6rem;padding-bottom:.35rem;border-bottom:1px solid var(--border)}
  .section-version{font-size:1rem;font-weight:700;color:var(--accent)}
  .section-meta{font-size:.8rem;color:var(--muted)}
  .entries{display:flex;flex-direction:column;gap:.5rem;margin-left:1rem}
  .entry{background:var(--card);border:1px solid var(--border);border-radius:8px;padding:.75rem 1rem}
  .entry-meta{font-size:.75rem;color:var(--muted);margin-bottom:.25rem}
  .entry-text{font-size:.93rem}
  .text-match{background:rgba(167,139,250,.18);border-radius:2px;padding:0 .15rem}
  .entity-grid{max-width:860px;margin:2rem auto 0;display:flex;flex-wrap:wrap;gap:.5rem}
  footer{max-width:860px;margin:3rem auto 0;font-size:.8rem;color:var(--muted);text-align:center}
"""


def _esc(s: str) -> str:
    return (
        s.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
    )


def entity_page_html(slug: str, meta: dict, entries: list, text_matched: set) -> str:
    name = meta["name"]
    desc = meta["desc"]
    total = len(entries)

    # Group entries by version, newest first
    by_version: dict = {}
    for e in entries:
        v = e["version"]
        if v not in by_version:
            by_version[v] = {"date": e["date"], "patch_title": e["patch_title"], "items": []}
        by_version[v]["items"].append(e)

    sorted_versions = sorted(by_version.items(), key=lambda x: x[1]["date"], reverse=True)

    sections = []
    for version, vd in sorted_versions:
        rows = []
        for e in vd["items"]:
            badge_html, _ = BADGE.get(e["type"], (e["type"], "#888"))
            entry_id = e.get("id", "")
            source_note = ""
            if entry_id in text_matched:
                source_note = ' <span class="text-match" title="Found via text mention, not tag">text</span>'
            rows.append(
                f'<div class="entry">'
                f'<div class="entry-meta">{badge_html}{source_note}</div>'
                f'<div class="entry-text">{_esc(e["text"])}</div>'
                f"</div>"
            )
        items_html = "\n".join(rows)
        sections.append(
            f'<div class="section">'
            f'<div class="section-head">'
            f'<a class="section-version" href="/patch/?v={version}">v{version}</a>'
            f'<span class="section-meta">{vd["patch_title"]} · {vd["date"]} · {len(vd["items"])} change{"s" if len(vd["items"])!=1 else ""}</span>'
            f"</div>"
            f'<div class="entries">{items_html}</div>'
            f"</div>"
        )

    body = "\n".join(sections)
    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>SpiritVale — {name} History</title>
<meta name="description" content="Complete patch history for {name} in SpiritVale across all versions.">
<meta property="og:title" content="SpiritVale — {name} History">
<meta property="og:description" content="{_esc(desc)} {total} changes across all patches.">
<meta property="og:url" content="https://spiritvale.tama.sh/entity/{slug}/">
<meta property="og:image" content="https://spiritvale.tama.sh/og/latest.png">
<link rel="icon" type="image/svg+xml" href="/favicon.svg">
<link rel="canonical" href="https://spiritvale.tama.sh/entity/{slug}/">
<style>{CSS}</style>
</head>
<body>
<header>
  <div class="breadcrumb"><a href="/">SpiritVale</a> › <a href="/entity/">Entities</a> › {name}</div>
  <h1>{name}</h1>
  <p class="subtitle">{total} change{"s" if total!=1 else ""} across {len(sorted_versions)} patch{"es" if len(sorted_versions)!=1 else ""}</p>
  <p class="desc">{_esc(desc)}</p>
</header>
{body}
<footer>
  <a href="/">Home</a> &middot; <a href="/search/">Search</a> &middot; <a href="/entity/">All Entities</a> &middot; <a href="/tag/">Tags</a>
</footer>
</body>
</html>"""


def entity_index_html(entity_counts: dict) -> str:
    cards = "".join(
        f'<a href="/entity/{slug}/" style="display:inline-flex;flex-direction:column;gap:.2rem;padding:.6rem 1rem;background:var(--card);border:1px solid var(--border);border-radius:8px;color:var(--fg)">'
        f'<span style="font-weight:600;color:var(--accent)">{ENTITIES[slug]["name"]}</span>'
        f'<span style="font-size:.8rem;color:var(--muted)">{count} changes</span>'
        f'<span style="font-size:.75rem;color:var(--muted);max-width:180px;white-space:normal">{_esc(ENTITIES[slug]["desc"][:60])}{"…" if len(ENTITIES[slug]["desc"])>60 else ""}</span>'
        f"</a>"
        for slug, count in sorted(entity_counts.items(), key=lambda x: -x[1])
    )
    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>SpiritVale — Entity History</title>
<meta name="description" content="Browse SpiritVale patch history by class, dungeon, or game system.">
<link rel="icon" type="image/svg+xml" href="/favicon.svg">
<link rel="canonical" href="https://spiritvale.tama.sh/entity/">
<style>{CSS}</style>
</head>
<body>
<header>
  <div class="breadcrumb"><a href="/">SpiritVale</a> › Entities</div>
  <h1>Entity History</h1>
  <p class="subtitle">Browse patch changes by class, dungeon, or system — cross-version balance delta</p>
</header>
<div class="entity-grid">{cards}</div>
<footer>
  <a href="/">Home</a> &middot; <a href="/search/">Search</a> &middot; <a href="/tag/">Tags</a>
</footer>
</body>
</html>"""


def main() -> None:
    with open(INDEX_PATH) as f:
        data = json.load(f)

    entries = data["entries"]

    # Map slug → (matched entries list, set of entry IDs matched via text only)
    by_entity: dict[str, list] = defaultdict(list)
    text_matched: dict[str, set] = defaultdict(set)
    seen: dict[str, set] = defaultdict(set)  # dedup by entry id per entity

    for entry in entries:
        entry_id = entry.get("id", "")
        entry_tags = set(entry.get("tags", []))
        text = entry.get("text", "")

        for slug, meta in ENTITIES.items():
            # Match via tag OR text keyword
            tag_hit = bool(meta["tags"] & entry_tags)
            text_hit = bool(meta["pattern"].search(text))

            if (tag_hit or text_hit) and entry_id not in seen[slug]:
                by_entity[slug].append(entry)
                seen[slug].add(entry_id)
                if text_hit and not tag_hit:
                    text_matched[slug].add(entry_id)

    os.makedirs(ENTITY_DIR, exist_ok=True)

    entity_counts: dict[str, int] = {}
    for slug, matched in by_entity.items():
        entity_counts[slug] = len(matched)
        slug_dir = os.path.join(ENTITY_DIR, slug)
        os.makedirs(slug_dir, exist_ok=True)
        page = entity_page_html(slug, ENTITIES[slug], matched, text_matched[slug])
        with open(os.path.join(slug_dir, "index.html"), "w") as f:
            f.write(page)

    with open(os.path.join(ENTITY_DIR, "index.html"), "w") as f:
        f.write(entity_index_html(entity_counts))

    manifest = {
        "generated_at": data["generated_at"],
        "entities": {
            slug: {
                "name": ENTITIES[slug]["name"],
                "count": cnt,
                "text_only_count": len(text_matched.get(slug, set())),
                "url": f"/entity/{slug}/",
            }
            for slug, cnt in sorted(entity_counts.items(), key=lambda x: -x[1])
        },
    }
    with open(os.path.join(ENTITY_DIR, "index.json"), "w") as f:
        json.dump(manifest, f, indent=2)

    total_text_only = sum(len(v) for v in text_matched.values())
    print(
        f"entity pages: {len(by_entity)} entities, "
        f"{sum(entity_counts.values())} total matched entries "
        f"({total_text_only} text-only, not in tags)",
        file=__import__("sys").stderr,
    )


if __name__ == "__main__":
    main()
