#!/usr/bin/env python3
"""
Fetch Steam AppNews for SpiritVale (app 3918510) and create draft patch files
for any items that look like patch notes and aren't already indexed.

Output (GITHUB_OUTPUT):
  new_draft=true|false
  slug=<slug>          (first new draft only)
  title=<title>        (first new draft only)
"""
import json
import os
import re
import sys
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

APPID = os.environ.get("STEAM_APPID", "3918510")
API_URL = (
    f"https://api.steampowered.com/ISteamNews/GetNewsForApp/v2/"
    f"?appid={APPID}&count=10&format=json"
)

INDEX_PATH = Path("patches/index.json")
PATCHES_DIR = Path("patches")

PATCH_KEYWORDS = re.compile(r"patch|update|hotfix|fix|build|release", re.IGNORECASE)
VERSION_RE = re.compile(r"v?(\d+\.\d+(?:\.\d+)?)")
HTML_TAGS = re.compile(r"<[^>]+>")


def fetch_news():
    req = urllib.request.Request(API_URL, headers={"User-Agent": "spiritvale-site/1.0"})
    with urllib.request.urlopen(req, timeout=20) as r:
        return json.loads(r.read())


def load_index():
    if INDEX_PATH.exists():
        return json.loads(INDEX_PATH.read_text())
    return {"latest_version": None, "versions": []}


def existing_news_ids(index):
    return {
        str(v["steam_news_id"])
        for v in index.get("versions", [])
        if v.get("steam_news_id")
    }


def existing_versions(index):
    return {v["version"] for v in index.get("versions", [])}


def extract_version(title):
    m = VERSION_RE.search(title)
    if not m:
        return None
    parts = m.group(1).split(".")
    while len(parts) < 3:
        parts.append("0")
    return ".".join(parts)


def title_to_slug(title):
    return re.sub(r"[^a-z0-9]+", "-", title.lower()).strip("-")[:40]


def strip_html(html):
    text = HTML_TAGS.sub("", html)
    # Collapse whitespace
    return re.sub(r"\s+", " ", text).strip()


def set_output(key, value):
    output_file = os.environ.get("GITHUB_OUTPUT", "")
    if output_file:
        with open(output_file, "a") as f:
            # Multiline values need special encoding; titles are single-line here
            f.write(f"{key}={value}\n")
    else:
        print(f"[output] {key}={value}")


def main():
    try:
        news_data = fetch_news()
    except Exception as e:
        print(f"ERROR: failed to fetch Steam news: {e}", file=sys.stderr)
        set_output("new_draft", "false")
        sys.exit(0)

    items = news_data.get("appnews", {}).get("newsitems", [])
    index = load_index()
    seen_gids = existing_news_ids(index)
    seen_versions = existing_versions(index)

    new_drafts = []

    for item in items:
        gid = str(item.get("gid", ""))
        title = item.get("title", "").strip()

        if gid in seen_gids:
            continue

        if not PATCH_KEYWORDS.search(title):
            continue

        version = extract_version(title)
        if version and version in seen_versions:
            continue

        slug = version or title_to_slug(title)
        draft_path = PATCHES_DIR / f"draft-{slug}.json"

        if draft_path.exists():
            continue

        pub_ts = item.get("date", 0)
        pub_dt = datetime.fromtimestamp(pub_ts, tz=timezone.utc)
        raw_body = strip_html(item.get("contents", ""))[:2000]
        item_url = item.get("url") or None

        draft = {
            "$schema": "/schema/patch.json",
            "version": version or "0.0.0",
            "title": title,
            "date": pub_dt.strftime("%Y-%m-%d"),
            "current": False,
            "url": item_url,
            "steam_news_id": gid,
            "released_at": pub_dt.isoformat(),
            "raw_body": raw_body,
            "added": [],
            "changed": [],
            "fixed": [],
            "removed": [],
        }

        draft_path.write_text(json.dumps(draft, indent=2, ensure_ascii=False) + "\n")
        print(f"Created: {draft_path}")
        new_drafts.append({"slug": slug, "title": title})

    if new_drafts:
        first = new_drafts[0]
        set_output("new_draft", "true")
        set_output("slug", first["slug"])
        # Strip newlines so the output line stays single-line
        safe_title = first["title"].replace("\n", " ").replace("\r", "")
        set_output("title", safe_title)
        print(f"{len(new_drafts)} new draft(s) created.")
    else:
        set_output("new_draft", "false")
        print("No new patch notes found.")


if __name__ == "__main__":
    main()
