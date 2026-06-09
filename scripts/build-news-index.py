#!/usr/bin/env python3
"""Build news/ namespace — announcement index, HTML listing, and Atom feed.

Pattern: warframestat.us /news/ — separate from patch versioning; covers
announcements, roadmaps, events. Source: patches/drafts/announcement-*.json.

Outputs:
  news/index.json   — machine-readable announcement list
  news/index.html   — human-readable listing page
  news/feed.xml     — Atom feed for announcement subscribers

Run: python3 scripts/build-news-index.py  OR  make news
"""
import json
import re
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).parent.parent
DRAFTS_DIR = ROOT / "patches" / "drafts"
NEWS_DIR = ROOT / "news"
BASE_URL = "https://spiritvale.tama.sh"

TYPE_LABEL = {
    "announcement": "Announcement",
    "event": "Event",
    "roadmap": "Roadmap",
}


def _slug(title: str, date_str: str) -> str:
    safe = re.sub(r"[^a-z0-9]+", "-", title.lower()).strip("-")[:50]
    return f"{date_str}-{safe}"


def _load_announcements() -> list[dict]:
    items = []
    for f in sorted(DRAFTS_DIR.glob("announcement-*.json"), reverse=True):
        try:
            d = json.loads(f.read_text())
        except json.JSONDecodeError:
            continue
        if d.get("type") != "announcement":
            continue
        slug = _slug(d.get("title", f.stem), d.get("date", "0000-00-00"))
        items.append({
            "slug": slug,
            "title": d.get("title", "Untitled"),
            "date": d.get("date", ""),
            "type": d.get("type", "announcement"),
            "steam_news_id": d.get("steam_news_id"),
            "steam_url": d.get("steam_url"),
            "raw_body": d.get("raw_body", ""),
            "_source_file": f.name,
        })
    return items


def build_json(items: list[dict]) -> None:
    out = {
        "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "count": len(items),
        "items": [
            {
                "slug": it["slug"],
                "title": it["title"],
                "date": it["date"],
                "type": it["type"],
                "url": f"{BASE_URL}/news/#{it['slug']}",
                "steam_url": it.get("steam_url"),
                "steam_news_id": it.get("steam_news_id"),
            }
            for it in items
        ],
    }
    (NEWS_DIR / "index.json").write_text(json.dumps(out, indent=2) + "\n")
    print(f"news/index.json written — {len(items)} announcements")


def build_feed(items: list[dict]) -> None:
    updated = f"{items[0]['date']}T00:00:00Z" if items else datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    entries = []
    for it in items:
        steam_link = f'\n    <link rel="related" href="{it["steam_url"]}" title="Steam Announcement" />' if it.get("steam_url") else ""
        body_escaped = it["raw_body"].replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
        entries.append(f"""  <entry>
    <id>{BASE_URL}/news/#{it["slug"]}</id>
    <title>{it["title"].replace("&", "&amp;").replace("<", "&lt;")}</title>
    <link rel="alternate" href="{BASE_URL}/news/#{it["slug"]}" />{steam_link}
    <updated>{it["date"]}T00:00:00Z</updated>
    <summary type="text">{body_escaped[:400]}</summary>
  </entry>""")

    xml = f"""<?xml version="1.0" encoding="UTF-8"?>
<feed xmlns="http://www.w3.org/2005/Atom">
  <id>{BASE_URL}/news/feed.xml</id>
  <title>SpiritVale News &amp; Announcements</title>
  <link rel="alternate" type="text/html" href="{BASE_URL}/news/" />
  <link rel="self" type="application/atom+xml" href="{BASE_URL}/news/feed.xml" />
  <updated>{updated}</updated>
  <author>
    <name>SpiritVale Dev</name>
  </author>

{chr(10).join(entries)}
</feed>
"""
    (NEWS_DIR / "feed.xml").write_text(xml)
    print(f"news/feed.xml written — {len(items)} entries")


def _paragraphs(text: str) -> list[str]:
    """Split Steam raw_body (no newlines) into readable paragraphs.

    Steam strips all newlines. We recover paragraph breaks by splitting on:
      - ".<Capital>"  (no space — common in Steam exports)
      - ". <Capital>" (with space)
      - "!<Capital>" / "! <Capital>"
    Each resulting chunk becomes its own <p>.
    """
    parts = re.split(r"[.!]\s*(?=[A-Z])", text)
    paras = []
    for p in parts:
        p = p.strip()
        if p:
            paras.append(p if re.search(r"[.!]$", p) else p + ".")
    return paras


def build_html(items: list[dict]) -> None:
    cards = []
    for it in items:
        steam_link = f'<a href="{it["steam_url"]}" class="steam-link" target="_blank" rel="noopener">Steam ↗</a>' if it.get("steam_url") else ""
        type_badge = TYPE_LABEL.get(it["type"], it["type"].title())
        raw = it["raw_body"]
        body_preview = raw[:280].replace("<", "&lt;").replace(">", "&gt;")
        if len(raw) > 280:
            body_preview += "…"
            paras = _paragraphs(raw)
            paras_html = "\n        ".join(
                f'<p class="body-full">{p.replace("<", "&lt;").replace(">", "&gt;")}</p>'
                for p in paras
            )
            body_html = f"""<p class="body">{body_preview}</p>
      <details class="body-expand">
        <summary>Read full announcement</summary>
        {paras_html}
      </details>"""
        else:
            body_html = f'<p class="body">{body_preview}</p>'
        cards.append(f"""    <article id="{it['slug']}" class="card">
      <header>
        <span class="badge">{type_badge}</span>
        <time datetime="{it['date']}">{it['date']}</time>
        {steam_link}
      </header>
      <h2>{it['title'].replace('<', '&lt;')}</h2>
      {body_html}
    </article>""")

    cards_html = "\n".join(cards) if cards else "    <p class='empty'>No announcements yet.</p>"

    og_desc = items[0]["raw_body"][:160].replace('"', "&quot;") if items else "SpiritVale news, announcements, roadmap updates, and events."
    og_title = items[0]["title"].replace('"', "&quot;") if items else "SpiritVale — News &amp; Announcements"

    html = f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>SpiritVale — News &amp; Announcements</title>
<meta name="description" content="SpiritVale news, announcements, roadmap updates, and events.">
<meta property="og:type" content="website">
<meta property="og:site_name" content="SpiritVale Patch Archive">
<meta property="og:url" content="{BASE_URL}/news/">
<meta property="og:title" content="{og_title}">
<meta property="og:description" content="{og_desc}">
<meta property="og:image" content="{BASE_URL}/og/v0.18.0.png">
<meta property="og:image:width" content="1200">
<meta property="og:image:height" content="630">
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:title" content="{og_title}">
<meta name="twitter:description" content="{og_desc}">
<meta name="twitter:image" content="{BASE_URL}/og/v0.18.0.png">
<link rel="icon" type="image/svg+xml" href="/favicon.svg">
<link rel="canonical" href="{BASE_URL}/news/">
<link rel="alternate" type="application/atom+xml" href="{BASE_URL}/news/feed.xml" title="SpiritVale News Feed">
<link rel="alternate" type="application/atom+xml" href="{BASE_URL}/feed.xml" title="SpiritVale Patch Notes Feed">
<style>
  :root {{
    --bg: #0a0612; --fg: #e8e3f0; --muted: #8b82a0;
    --accent: #a78bfa; --accent-2: #7c3aed;
    --card: rgba(167,139,250,0.08); --border: rgba(167,139,250,0.2);
  }}
  * {{ box-sizing: border-box; margin: 0; padding: 0; }}
  body {{ font-family: -apple-system, BlinkMacSystemFont, "Inter", "Noto Sans Thai", sans-serif; background: var(--bg); color: var(--fg); line-height: 1.6; padding: 2rem 1rem; }}
  .container {{ max-width: 720px; margin: 0 auto; }}
  header.page-header {{ margin-bottom: 2rem; }}
  header.page-header h1 {{ font-size: 1.75rem; color: var(--accent); }}
  header.page-header p {{ color: var(--muted); margin-top: .4rem; }}
  nav {{ margin-top: .75rem; }}
  nav a {{ color: var(--accent); text-decoration: none; font-size: .875rem; }}
  nav a:hover {{ text-decoration: underline; }}
  nav a + a {{ margin-left: 1.25rem; }}
  .feed-link {{ display:inline-block; margin-top:.5rem; font-size:.8rem; color:var(--muted); }}
  .feed-link a {{ color: var(--accent); }}
  .card {{ background: var(--card); border: 1px solid var(--border); border-radius: 8px; padding: 1.25rem; margin-bottom: 1.25rem; }}
  .card header {{ display:flex; align-items:center; gap:.75rem; margin-bottom:.6rem; flex-wrap:wrap; }}
  .badge {{ background: var(--accent-2); color: #fff; font-size:.72rem; padding:.15em .55em; border-radius:4px; text-transform:uppercase; letter-spacing:.04em; }}
  time {{ color: var(--muted); font-size:.85rem; }}
  .steam-link {{ margin-left: auto; color: var(--accent); font-size:.85rem; text-decoration:none; }}
  .steam-link:hover {{ text-decoration:underline; }}
  h2 {{ font-size:1.1rem; margin-bottom:.5rem; }}
  .body {{ color: var(--muted); font-size:.9rem; }}
  .body-expand {{ margin-top:.5rem; }}
  .body-expand summary {{ color: var(--accent); font-size:.85rem; cursor:pointer; user-select:none; }}
  .body-expand summary:hover {{ text-decoration:underline; }}
  .body-full {{ color: var(--muted); font-size:.9rem; margin-top:.5rem; }}
  .body-full + .body-full {{ margin-top:.5rem; }}
  .empty {{ color: var(--muted); text-align:center; padding: 2rem; }}
  footer {{ color: var(--muted); font-size:.8rem; text-align:center; margin-top: 2.5rem; }}
  footer a {{ color: var(--accent); }}
</style>
</head>
<body>
<div class="container">
  <header class="page-header">
    <h1>SpiritVale — News &amp; Announcements</h1>
    <p>Official roadmap updates, events, and developer announcements.</p>
    <nav>
      <a href="/">Home</a>
      <a href="/patch/">Patch Notes</a>
      <a href="/search/">Search</a>
    </nav>
    <p class="feed-link">Subscribe: <a href="/news/feed.xml">Atom feed</a></p>
  </header>

  <main>
{cards_html}
  </main>

  <footer>
    <p>Data sourced from Steam Announcements &middot; <a href="/patches/index.json">Patch Index</a> &middot; <a href="/api/health.json">Health</a></p>
  </footer>
</div>
</body>
</html>
"""
    (NEWS_DIR / "index.html").write_text(html)
    print(f"news/index.html written — {len(items)} cards")


def main():
    NEWS_DIR.mkdir(exist_ok=True)
    items = _load_announcements()
    build_json(items)
    build_feed(items)
    build_html(items)
    print(f"Done — news/ namespace built ({len(items)} announcements)")


if __name__ == "__main__":
    main()
