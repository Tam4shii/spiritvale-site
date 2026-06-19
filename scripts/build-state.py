#!/usr/bin/env python3
"""Build state.json — worldstate aggregation endpoint.

Single-response summary: latest patch + index summary + health + draft status +
deadline alerts + stats totals. Collapses 3 client round-trips to 1.

Pattern: warframestat.us /pc worldstate — single fetch gives clients everything
they need to decide whether to poll further.

Accessible at:
  /state.json          (root)
  /v1/state.json       (versioned alias via _redirects /v1/* rewrite)

Run: python3 scripts/build-state.py  OR  make state
"""
import json
from datetime import date, datetime, timezone
from pathlib import Path

ROOT = Path(__file__).parent.parent
# state/last-poll.json is gitignored — monitoring runs write it locally but CI/fresh clones
# never have it. Mirror the dual-source pattern from build-health.py: prefer the fresher
# timestamp between patches/index.json and last-poll.json so state.json stays accurate on
# both environments without requiring the gitignored file to exist.
LAST_POLL_PATH = ROOT / "state" / "last-poll.json"

# Known game milestones — update when developer posts new dates.
_MILESTONES = [
    {"key": "playtest-end", "label": "Playtest ended / progress wipe", "date": "2026-06-08", "phase": "playtest-end"},
    {"key": "demo",         "label": "Steam Demo launch",              "date": "2026-06-12", "phase": "demo"},
    {"key": "early-access", "label": "Early Access launch",            "date": "2026-07-15", "phase": "early-access", "price_usd": 15.00},
]


def _load(path: Path) -> dict | list | None:
    try:
        with open(path) as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return None


def _best_poll_ts(index_ts: str | None) -> str | None:
    """Return whichever of index.json or last-poll.json carries the fresher timestamp."""
    try:
        lp = json.loads(LAST_POLL_PATH.read_text())
        file_ts = lp.get("polled_at")
        if file_ts and (not index_ts or file_ts > index_ts):
            return file_ts
    except (FileNotFoundError, json.JSONDecodeError, TypeError):
        pass  # clean clone / CI — expected; fall through to index.json value
    return index_ts


def main():
    now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    patches_index = _load(ROOT / "patches" / "index.json") or {}
    latest_version = patches_index.get("latest_version")

    # Dual-source last_polled_at — mirrors build-health.py fallback pattern.
    # patches/index.json is only updated by GH Actions; local monitoring runs
    # write state/last-poll.json (gitignored). Use whichever is more recent.
    _index_ts = patches_index.get("last_polled_at")
    last_poll_file = _load(ROOT / "state" / "last-poll.json") or {}
    _file_ts = last_poll_file.get("polled_at")
    if _file_ts and (not _index_ts or _file_ts > _index_ts):
        last_polled_at = _file_ts
    else:
        last_polled_at = _index_ts

    latest_entry = next(
        (v for v in patches_index.get("versions", []) if v.get("current")),
        None,
    )

    health = _load(ROOT / "api" / "health.json") or {}
    stats = _load(ROOT / "stats.json") or {}
    draft_seen = _load(ROOT / "state" / "draft-seen-counts.json") or {}
    deadline_status = _load(ROOT / "state" / "deadline-status.json") or {}

    pending_drafts = [
        {"filename": k, **v} for k, v in draft_seen.items()
    ]

    today = datetime.now(timezone.utc).date()
    milestones_with_days = []
    for m in _MILESTONES:
        m_date = date.fromisoformat(m["date"])
        days_until = (m_date - today).days
        entry = {**m, "days_until": days_until, "past": days_until < 0}
        milestones_with_days.append(entry)
    upcoming = [m for m in milestones_with_days if not m["past"]]
    next_milestone = upcoming[0] if upcoming else None

    state = {
        "generated_at": now,
        "latest_version": latest_version,
        "last_polled_at": last_polled_at,
        "poll_tz": patches_index.get("poll_tz", "UTC"),
        "latest": {
            "version": latest_entry.get("version"),
            "title": latest_entry.get("title"),
            "date": latest_entry.get("date"),
            "change_counts": latest_entry.get("change_counts"),
            "archive_url": latest_entry.get("archive_url"),
            "steam_news_id": latest_entry.get("steam_news_id"),
        } if latest_entry else None,
        "index_summary": {
            "total_versions": len(patches_index.get("versions", [])),
            "items_found": patches_index.get("items_found"),
        },
        "health": {
            "severity": health.get("severity"),
            "stale": health.get("stale"),
            "hours_since_poll": health.get("hours_since_poll"),
            "message": health.get("message"),
            "steam_baseline_match": health.get("steam_baseline_match"),
        },
        "stats_summary": {
            "total_patches": stats.get("total_patches"),
            "total_entries": stats.get("total_entries"),
            "change_totals": stats.get("change_totals"),
            "avg_days_between_patches": stats.get("avg_days_between_patches"),
        },
        "pending_drafts": pending_drafts,
        "pending_drafts_count": len(pending_drafts),
        "deadline_alerts": deadline_status.get("deadlines", []),
        "worst_deadline_severity": deadline_status.get("worst_severity"),
        "milestones": milestones_with_days,
        "upcoming_milestones": upcoming,
        "next_milestone": next_milestone,
        "_links": {
            "latest": "/patches/latest.json",
            "index": "/patches/index.json",
            "health": "/api/health.json",
            "stats": "/stats.json",
            "search": "/search-index.json",
            "diff_index": "/diff/index.json",
            "openapi": "/v1/openapi.json",
        },
    }

    out_path = ROOT / "state.json"
    with open(out_path, "w") as f:
        json.dump(state, f, indent=2)
        f.write("\n")

    deadline_count = len(state["deadline_alerts"])
    worst = state["worst_deadline_severity"] or "none"
    print(
        f"state.json written — latest={latest_version}, "
        f"severity={health.get('severity')}, "
        f"pending_drafts={len(pending_drafts)}, "
        f"deadline_alerts={deadline_count} (worst={worst})"
    )


if __name__ == "__main__":
    main()
