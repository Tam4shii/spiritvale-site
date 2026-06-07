#!/usr/bin/env python3
"""
Fetch Steam AppNews for SpiritVale (app 3918510) and create draft patch files
for any items that look like patch notes and aren't already indexed.

Output (GITHUB_OUTPUT):
  new_draft=true|false        semver-versioned game update found (triggers PR + patch pipeline)
  slug=<slug>                 first new *patch* draft only (requires new_draft=true)
  title=<title>               first new *patch* draft only (requires new_draft=true)

  new_announcement=true|false non-semver Steam post matched PATCH_KEYWORDS (e.g. release dates,
                              wipe notices, Next Fest announcements). Draft written to
                              patches/drafts/announcement-<slug>.json — NOT a patch entry.
                              new_draft=false is expected when only announcements are found.
  announcement_slug=<slug>    first announcement draft only (requires new_announcement=true)
  announcement_title=<title>  first announcement draft only (requires new_announcement=true)
"""
import json
import os
import re
import subprocess
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
# Tracks how many poll cycles each unreviewed draft has been sitting — signals staleness
SEEN_COUNTS_PATH = Path("state/draft-seen-counts.json")
# Escalation thresholds for unreviewed drafts (poll cycles = runs of make check-steam / GH Actions daily cron).
STALE_ALERT_CYCLES = 3   # seen_count >= this → push luna-tg notification to boss
STALE_ARCHIVE_CYCLES = 7  # seen_count >= this → notification recommends auto-archive
STALE_DRAFT_CYCLES = STALE_ALERT_CYCLES  # backward-compat alias (used in stale list filter below)

# PR #1 deadline escalation — separate [URGENT] path, independent of routine stale-draft alert.
# Fire when hours-to-deadline <= threshold so boss sees a distinct call-to-action, not just a stale-draft ping.
PR1_DEADLINE_STR = "2026-06-08"  # playtest ends — merge/close decision needed before this date
PR1_URL = "https://github.com/Tam4shii/spiritvale-site/pull/1"
URGENT_HOURS_THRESHOLD = 48  # hours remaining before deadline → escalate to [URGENT]
URGENT_DEDUP_HOURS = 6       # hours between re-fires of the [URGENT] message (shorter than stale 12h)
PERSISTENT_BLOCKERS_PATH = Path("state/persistent-blockers.json")

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


def load_seen_counts() -> dict:
    if SEEN_COUNTS_PATH.exists():
        return json.loads(SEEN_COUNTS_PATH.read_text())
    return {}


def save_seen_counts(counts: dict) -> None:
    SEEN_COUNTS_PATH.parent.mkdir(parents=True, exist_ok=True)
    SEEN_COUNTS_PATH.write_text(json.dumps(counts, indent=2) + "\n")
    print(f"WROTE: {SEEN_COUNTS_PATH} ({len(counts)} tracked draft(s))")


def bump_seen_count(counts: dict, draft_name: str, polled_at: str) -> None:
    """Increment the stale-draft counter for a draft that exists but hasn't been reviewed."""
    entry = counts.get(draft_name, {"seen_count": 0, "first_seen_at": polled_at})
    entry["seen_count"] = entry.get("seen_count", 0) + 1
    entry["last_seen_at"] = polled_at
    counts[draft_name] = entry


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


def fire_stale_alert(stale_name: str, stale_entry: dict, polled_at: str) -> bool:
    """Send a luna-tg push notification for an unreviewed draft.

    Deduplicates via alerted_at — skips if a notification was sent within the last 12 hours.
    Escalates message severity when seen_count >= STALE_ARCHIVE_CYCLES.
    Returns True if notification was sent (caller must set seen_counts_dirty).
    """
    count = stale_entry.get("seen_count", 0)
    last_alerted = stale_entry.get("alerted_at", "")

    if last_alerted:
        try:
            last_dt = datetime.fromisoformat(last_alerted.replace("Z", "+00:00"))
            now_dt = datetime.now(tz=timezone.utc)
            if (now_dt - last_dt).total_seconds() < 43200:  # 12-hour dedup window
                print(f"[stale-alert] suppressed — already alerted at {last_alerted[:16]}, <12h ago")
                return False
        except Exception:
            pass

    suggest_archive = count >= STALE_ARCHIVE_CYCLES
    severity = "🔴🔴" if suggest_archive else "🔴"
    action = (
        "Draft sitting too long — consider closing PR + archiving."
        if suggest_archive
        else "Action needed: merge / close PR / leave draft."
    )
    msg = (
        f"{severity} SpiritVale: Stale draft unreviewed\n"
        f"Draft: {stale_name}\n"
        f"Seen: {count} poll cycles "
        f"(first: {stale_entry.get('first_seen_at', '?')[:10]})\n"
        f"PR #1 → https://github.com/Tam4shii/spiritvale-site/pull/1\n"
        f"{action}"
    )

    luna_tg = Path.home() / ".local/bin/luna-tg"
    if not luna_tg.is_file():
        print(f"WARN: luna-tg not found at {luna_tg} — stale alert skipped", file=sys.stderr)
        return False

    try:
        subprocess.run([str(luna_tg), msg], check=True, timeout=10)
        stale_entry["alerted_at"] = polled_at
        print(f"[stale-alert] notification sent for {stale_name} (count={count})")
        return True
    except Exception as e:
        print(f"WARN: stale alert send failed: {e}", file=sys.stderr)
        return False


def load_persistent_blockers() -> dict:
    if PERSISTENT_BLOCKERS_PATH.exists():
        return json.loads(PERSISTENT_BLOCKERS_PATH.read_text())
    return {}


def save_persistent_blockers(blockers: dict) -> None:
    PERSISTENT_BLOCKERS_PATH.parent.mkdir(parents=True, exist_ok=True)
    PERSISTENT_BLOCKERS_PATH.write_text(json.dumps(blockers, indent=2) + "\n")
    print(f"WROTE: {PERSISTENT_BLOCKERS_PATH} ({len(blockers)} blocker(s))")


def fire_pr1_deadline_alert(blockers: dict, polled_at: str) -> bool:
    """Fire a distinct [URGENT] Telegram alert when PR #1 deadline is ≤48h away.

    This is intentionally separate from fire_stale_alert so the boss sees a
    dedicated call-to-action with a specific deadline, not just a generic stale ping.
    Returns True if notification was sent (caller must then save_persistent_blockers).
    """
    try:
        deadline_dt = datetime.fromisoformat(PR1_DEADLINE_STR).replace(tzinfo=timezone.utc)
    except Exception as e:
        print(f"WARN: could not parse PR1_DEADLINE_STR={PR1_DEADLINE_STR!r}: {e}", file=sys.stderr)
        return False

    now_dt = datetime.now(tz=timezone.utc)
    hours_remaining = (deadline_dt - now_dt).total_seconds() / 3600

    if hours_remaining > URGENT_HOURS_THRESHOLD:
        print(
            f"[pr1-deadline] {hours_remaining:.1f}h remaining — above {URGENT_HOURS_THRESHOLD}h threshold, no urgent alert"
        )
        return False

    # Dedup: skip if we already fired an [URGENT] alert within URGENT_DEDUP_HOURS
    pr1 = blockers.get("pr1", {})
    last_urgent = pr1.get("last_urgent_at", "")
    if last_urgent:
        try:
            last_dt = datetime.fromisoformat(last_urgent.replace("Z", "+00:00"))
            if (now_dt - last_dt).total_seconds() < URGENT_DEDUP_HOURS * 3600:
                print(
                    f"[pr1-deadline] suppressed — already sent [URGENT] at {last_urgent[:16]}, "
                    f"<{URGENT_DEDUP_HOURS}h ago"
                )
                return False
        except Exception:
            pass

    time_str = (
        f"{hours_remaining:.0f}h remaining"
        if hours_remaining >= 0
        else f"OVERDUE by {abs(hours_remaining):.0f}h"
    )
    msg = (
        f"🔴 [URGENT] SpiritVale PR #1 — DECISION NEEDED\n"
        f"Playtest ends {PR1_DEADLINE_STR} — {time_str}\n"
        f"  merge → publishes /news page\n"
        f"  close → archives (no news page)\n"
        f"PR: {PR1_URL}"
    )

    luna_tg = Path.home() / ".local/bin/luna-tg"
    if not luna_tg.is_file():
        print(f"WARN: luna-tg not found at {luna_tg} — PR1 urgent alert skipped", file=sys.stderr)
        return False

    try:
        subprocess.run([str(luna_tg), msg], check=True, timeout=10)
        if "pr1" not in blockers:
            blockers["pr1"] = {"first_seen_at": polled_at, "alert_count": 0}
        blockers["pr1"]["last_urgent_at"] = polled_at
        blockers["pr1"]["alert_count"] = blockers["pr1"].get("alert_count", 0) + 1
        print(f"[pr1-deadline] [URGENT] alert sent ({time_str}, alert #{blockers['pr1']['alert_count']})")
        return True
    except Exception as e:
        print(f"WARN: PR1 urgent alert failed: {e}", file=sys.stderr)
        return False


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
    # Emit source path so log readers can verify without guessing the file location.
    # count= is the STEAM_NEWS_COUNT constant passed to the Steam API, not a dynamic total.
    print(f"[baseline] {BASELINE_PATH}: version={prev_version}, count={prev_count}/{STEAM_NEWS_COUNT}")
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

    # Pre-compute timestamp so stale-count bumps and new draft writes share the same polled_at.
    polled_at = datetime.now(tz=timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    seen_counts = load_seen_counts()
    seen_counts_dirty = False

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

        # Announcements (no semver in title) go to patches/drafts/ with a distinct prefix
        # so new_draft=true remains exclusively for semver-versioned game updates.
        is_announcement = version is None
        slug = version or title_to_slug(title)
        if is_announcement:
            draft_path = PATCHES_DIR / "drafts" / f"announcement-{slug}.json"
        else:
            draft_path = PATCHES_DIR / f"draft-{slug}.json"

        if draft_path.exists():
            # Draft already written but not yet reviewed — bump staleness counter
            bump_seen_count(seen_counts, draft_path.name, polled_at)
            seen_counts_dirty = True
            continue

        pub_ts = item.get("date", 0)
        pub_dt = datetime.fromtimestamp(pub_ts, tz=timezone.utc)
        raw_body = strip_html(item.get("contents", ""))[:2000]
        steam_url = item.get("url") or None

        draft: dict = {
            "$schema": "/schema/patch.json",
            "version": version or "0.0.0",
            "title": title,
            "date": pub_dt.strftime("%Y-%m-%d"),
            "current": False,
            "url": None,
            "steam_news_id": gid,
            "steam_url": steam_url,
            "released_at": pub_dt.isoformat(),
            "raw_body": raw_body,
            "added": [],
            "changed": [],
            "fixed": [],
            "removed": [],
        }
        if is_announcement:
            # Announcements are not semver patches — skip semver validation downstream
            draft["type"] = "announcement"

        draft_path.parent.mkdir(parents=True, exist_ok=True)
        draft_path.write_text(json.dumps(draft, indent=2, ensure_ascii=False) + "\n")
        print(f"Created: {draft_path}")
        new_drafts.append({"slug": slug, "title": title, "is_announcement": is_announcement})

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

    patch_drafts = [d for d in new_drafts if not d.get("is_announcement")]
    announcement_drafts = [d for d in new_drafts if d.get("is_announcement")]

    if new_drafts:
        # Content changed — update committed artifacts
        try:
            stamp_index(polled_at, len(items))
            save_baseline(len(items), cur_version, polled_at)
        except Exception as e:
            print(f"WARN: could not update committed state: {e}", file=sys.stderr)
        print(
            f"[{polled_at}] mode=draft-created, "
            f"{len(patch_drafts)} patch draft(s), {len(announcement_drafts)} announcement draft(s)."
        )

    # new_draft=true ↔ a semver-versioned game update was found (triggers PR + patch pipeline).
    # new_announcement=true ↔ a non-semver Steam post matched PATCH_KEYWORDS (e.g. release date
    # news, wipe announcements) — stored in patches/drafts/announcement-*.json, NOT as a patch.
    if patch_drafts:
        first = patch_drafts[0]
        set_output("new_draft", "true")
        set_output("slug", first["slug"])
        safe_title = first["title"].replace("\n", " ").replace("\r", "")
        set_output("title", safe_title)
    else:
        set_output("new_draft", "false")

    if announcement_drafts:
        first_ann = announcement_drafts[0]
        set_output("new_announcement", "true")
        set_output("announcement_slug", first_ann["slug"])
        safe_ann_title = first_ann["title"].replace("\n", " ").replace("\r", "")
        set_output("announcement_title", safe_ann_title)
        # Prominent local callout — CI fires Discord; local runs must surface this visually.
        # new_draft=false is CORRECT here (no semver patch); new_announcement=true is the signal.
        ann_paths = [
            f"  patches/drafts/announcement-{d['slug']}.json" for d in announcement_drafts
        ]
        print(
            "\n"
            "╔══════════════════════════════════════════════════════════════╗\n"
            "║  [BOSS ACTION] STEAM ANNOUNCEMENT DETECTED                   ║\n"
            "╠══════════════════════════════════════════════════════════════╣\n"
            f"║  Title : {safe_ann_title[:52]:<52} ║\n"
            f"║  Count : {len(announcement_drafts):<52} ║\n"
            "║  Files :                                                     ║\n"
            + "".join(f"║    {p:<58} ║\n" for p in ann_paths)
            + "╠══════════════════════════════════════════════════════════════╣\n"
            "║  new_draft=false is CORRECT — no semver patch was released.  ║\n"
            "║  Review draft → publish / archive / ignore.                  ║\n"
            "║  See: patches/drafts/README.md                               ║\n"
            "╚══════════════════════════════════════════════════════════════╝"
        )
    else:
        set_output("new_announcement", "false")

    if seen_counts_dirty:
        save_seen_counts(seen_counts)

    # PR #1 deadline escalation — fires [URGENT] Telegram when ≤48h to playtest end.
    # Separate from the routine stale-draft alert so boss sees a distinct call-to-action.
    blockers = load_persistent_blockers()
    if fire_pr1_deadline_alert(blockers, polled_at):
        save_persistent_blockers(blockers)

    # Stale escalation — re-ping Discord for any draft stuck ≥ STALE_DRAFT_CYCLES poll cycles.
    # Gives the boss an actionable nudge with a concrete timeout, rather than silent "awaiting review".
    stale = [
        (name, entry)
        for name, entry in seen_counts.items()
        if entry.get("seen_count", 0) >= STALE_DRAFT_CYCLES
    ]
    if stale:
        stale_name, stale_entry = stale[0]
        set_output("stale_draft", "true")
        set_output("stale_draft_slug", stale_name)
        set_output("stale_draft_cycles", str(stale_entry.get("seen_count", 0)))
        set_output("stale_draft_first_seen", stale_entry.get("first_seen_at", ""))
        print(
            f"[stale-escalation] {stale_name} has been unreviewed for "
            f"{stale_entry.get('seen_count', 0)} cycles "
            f"(first seen: {stale_entry.get('first_seen_at', 'unknown')})"
        )
        # 🔴 Push notification: alert boss when draft sits past STALE_ALERT_CYCLES.
        # Deduplicates via alerted_at (12h window) — safe to call on every poll run.
        # IMPORTANT: save_seen_counts runs before this block so alerted_at must be
        # persisted here explicitly; otherwise the 12h dedup never takes effect and
        # the notification either fires on every run or silently re-fires after restart.
        if fire_stale_alert(stale_name, stale_entry, polled_at):
            save_seen_counts(seen_counts)  # persist alerted_at for dedup
    else:
        set_output("stale_draft", "false")

    if not new_drafts:
        # No new drafts — skip committed writes to avoid no-op commit noise.
        # Update baseline only when count or version actually changed (drift signal).
        baseline = load_baseline()
        if baseline.get("count") != len(items) or baseline.get("latest_version") != cur_version:
            try:
                save_baseline(len(items), cur_version, polled_at)
            except Exception as e:
                print(f"WARN: could not update baseline: {e}", file=sys.stderr)
        # Emit both sides of every comparison so a log excerpt is self-verifying
        # without needing to cross-reference a prior run.
        b_version = baseline.get("latest_version", "n/a")
        b_count = baseline.get("count")
        b_count_str = str(b_count) if b_count is not None else "n/a"
        count_verdict = "→ no change" if b_count == len(items) else f"→ CHANGED (was {b_count_str})"
        print(
            f"[{polled_at}] mode=poll-only (no new items). "
            f"version: {b_version} → {cur_version} (no change). "
            f"newsitems: {len(items)} (prev: {b_count_str}) {count_verdict}"
        )


if __name__ == "__main__":
    main()
