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
# How many items we request from Steam — also the baseline we expect back.
STEAM_NEWS_COUNT = 10
API_URL = (
    f"https://api.steampowered.com/ISteamNews/GetNewsForApp/v2/"
    f"?appid={APPID}&count={STEAM_NEWS_COUNT}&format=json"
)

INDEX_PATH = Path("patches/index.json")
PATCHES_DIR = Path("patches")
BASELINE_PATH = Path("state/steam-news-baseline.json")
# Ephemeral poll timestamp — gitignored, never commits, updated every run
POLL_STATE_PATH = Path("state/last-poll.json")

PATCH_KEYWORDS = re.compile(r"patch|update|hotfix|fix|build|release", re.IGNORECASE)
VERSION_RE = re.compile(r"v?(\d+\.\d+(?:\.\d+)?)")
HTML_TAGS = re.compile(r"<[^>]+>")
# Covers Steam BB-code: [b], [i], [u], [strike], [h1]-[h3], [list], [*], [url=...],
# [img], [previewyoutube], [table], [tr], [td], [code], [quote], [spoiler], and their
# closing counterparts. [*] (list bullet, no closing tag) requires the |\* branch.
# [url=URL]text[/url] → strips both tags, preserves anchor text only (URL is dropped;
# text is sufficient for draft classification and links can be resolved via steam_url).
# Sample: "[b]Fix[/b]: [list][*]Item[/list]" → "Fix: Item"
BB_TAGS = re.compile(r"\[/?(?:\*|[a-z][a-z0-9]*)(?:=[^\]]+)?\]", re.IGNORECASE)


def fetch_news():
    req = urllib.request.Request(API_URL, headers={"User-Agent": "spiritvale-site/1.0"})
    with urllib.request.urlopen(req, timeout=20) as r:
        status = r.status
        body = r.read()
        data = json.loads(body)
        item_count = len(data.get("appnews", {}).get("newsitems", []))
        print(f"[steam-api] HTTP {status}, newsitems={item_count}")
        return data


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
    text = BB_TAGS.sub("", text)
    return re.sub(r"\s+", " ", text).strip()


def set_output(key, value):
    output_file = os.environ.get("GITHUB_OUTPUT", "")
    if output_file:
        with open(output_file, "a") as f:
            # Multiline values need special encoding; titles are single-line here
            f.write(f"{key}={value}\n")
    else:
        print(f"[output] {key}={value}")


def stamp_index(polled_at: str, items_found: int) -> None:
    """Persist poll timestamp and item count into patches/index.json for audit trail."""
    if not INDEX_PATH.exists():
        return
    data = json.loads(INDEX_PATH.read_text())
    data["last_polled_at"] = polled_at
    data["items_found"] = items_found
    INDEX_PATH.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n")
    print(f"WROTE: {INDEX_PATH} (last_polled_at → {polled_at}, items_found={items_found})")


def load_baseline() -> dict:
    if BASELINE_PATH.exists():
        return json.loads(BASELINE_PATH.read_text())
    return {}


def save_baseline(count: int, version: str, checked_at: str) -> None:
    BASELINE_PATH.parent.mkdir(parents=True, exist_ok=True)
    data = {"count": count, "latest_version": version, "checked_at": checked_at}
    BASELINE_PATH.write_text(json.dumps(data, indent=2) + "\n")
    print(f"WROTE: {BASELINE_PATH} (count={count}, version={version})")


def _write_poll_state(
    polled_at: str,
    items_found: int,
    latest_item_id: str | None = None,
    latest_item_title: str | None = None,
) -> None:
    """Write ephemeral poll state to a gitignored file (never commits).

    Includes latest_item_id/title as a concrete anchor so auditors can confirm
    which article Steam returned most recently without re-running the poll.
    """
    try:
        POLL_STATE_PATH.parent.mkdir(parents=True, exist_ok=True)
        state: dict = {"polled_at": polled_at, "items_found": items_found}
        if latest_item_id is not None:
            state["latest_item_id"] = latest_item_id
        if latest_item_title is not None:
            state["latest_item_title"] = latest_item_title
        POLL_STATE_PATH.write_text(json.dumps(state, indent=2) + "\n")
    except Exception as e:
        print(f"WARN: could not write poll state: {e}", file=sys.stderr)


def check_baseline_delta(current_count: int, index: dict) -> None:
    """Warn if newsitems count changed without a version bump — early-signal check."""
    if current_count != STEAM_NEWS_COUNT:
        print(
            f"WARN: expected {STEAM_NEWS_COUNT} items (count= param) but got {current_count} "
            f"— Steam pagination or item removal may have occurred",
            file=sys.stderr,
        )
    baseline = load_baseline()
    if not baseline:
        return
    prev_count = baseline.get("count")
    prev_version = baseline.get("latest_version")
    cur_version = index.get("latest_version")
    if prev_count is not None and current_count != prev_count:
        if cur_version == prev_version:
            print(
                f"WARN: newsitems count changed {prev_count} → {current_count} "
                f"without version bump (still {cur_version}) — possible stealth update",
                file=sys.stderr,
            )
        else:
            print(f"[baseline] count {prev_count} → {current_count}, version {prev_version} → {cur_version}")


def main():
    try:
        news_data = fetch_news()
    except Exception as e:
        print(f"ERROR: failed to fetch Steam news: {e}", file=sys.stderr)
        set_output("new_draft", "false")
        sys.exit(0)

    items = news_data.get("appnews", {}).get("newsitems", [])
    index = load_index()
    check_baseline_delta(len(items), index)
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
        steam_url = item.get("url") or None

        draft = {
            "$schema": "/schema/patch.json",
            "version": version or "0.0.0",
            "title": title,
            "date": pub_dt.strftime("%Y-%m-%d"),
            "current": False,
            "url": None,           # Claude artifact URL — set manually after publishing
            "steam_news_id": gid,
            "steam_url": steam_url,  # canonical upstream Steam announcement URL
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

    polled_at = datetime.now(tz=timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    cur_version = index.get("latest_version", "unknown")

    # Always write ephemeral poll state (gitignored — no commit noise on every run).
    # Anchor on the first item so auditors know exactly which Steam article was top-of-feed.
    top = items[0] if items else {}
    _write_poll_state(
        polled_at,
        len(items),
        latest_item_id=str(top.get("gid", "")) or None,
        latest_item_title=top.get("title", "").strip() or None,
    )

    if new_drafts:
        # Content changed — update committed artifacts
        try:
            stamp_index(polled_at, len(items))
            save_baseline(len(items), cur_version, polled_at)
        except Exception as e:
            print(f"WARN: could not update committed state: {e}", file=sys.stderr)
        first = new_drafts[0]
        set_output("new_draft", "true")
        set_output("slug", first["slug"])
        safe_title = first["title"].replace("\n", " ").replace("\r", "")
        set_output("title", safe_title)
        print(f"[{polled_at}] mode=draft-created, {len(new_drafts)} new draft(s).")
    else:
        # No new drafts — skip committed writes to avoid no-op commit noise.
        # Update baseline only when count or version actually changed (drift signal).
        baseline = load_baseline()
        if baseline.get("count") != len(items) or baseline.get("latest_version") != cur_version:
            try:
                save_baseline(len(items), cur_version, polled_at)
            except Exception as e:
                print(f"WARN: could not update baseline: {e}", file=sys.stderr)
        set_output("new_draft", "false")
        print(f"[{polled_at}] mode=poll-only (no new items). Latest indexed: {cur_version}")


if __name__ == "__main__":
    main()
