#!/usr/bin/env python3
"""Generate stats.json — aggregated analytics artifact.

Reads patches/index.json (change counts, dates) and tag/index.json (tag counts)
and writes stats.json to the site root for LLM / Discord bot consumption.

Run: python3 scripts/build-stats.py  OR  make stats
"""
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).parent.parent

def load(path: Path) -> dict:
    with open(path) as f:
        return json.load(f)

def compute_cadence_days(versions: list) -> list:
    """Return list of {version, date, days_since_prev} sorted oldest-first."""
    dated = sorted(versions, key=lambda v: v["date"])
    result = []
    for i, v in enumerate(dated):
        if i == 0:
            days = None
        else:
            prev_dt = datetime.fromisoformat(dated[i - 1]["date"])
            curr_dt = datetime.fromisoformat(v["date"])
            days = (curr_dt - prev_dt).days
        result.append({"version": v["version"], "date": v["date"], "days_since_prev": days})
    return result

def main():
    index = load(ROOT / "patches" / "index.json")
    tag_index = load(ROOT / "tag" / "index.json")

    versions = index["versions"]

    # aggregate change counts across all patches
    totals = {"added": 0, "changed": 0, "fixed": 0, "removed": 0}
    for v in versions:
        cc = v.get("change_counts", {})
        for k in totals:
            totals[k] += cc.get(k, 0)

    cadence = compute_cadence_days(versions)
    intervals = [c["days_since_prev"] for c in cadence if c["days_since_prev"] is not None]
    avg_cadence = round(sum(intervals) / len(intervals), 1) if intervals else None

    # top tags sorted by count desc, take top 10
    tags_raw = tag_index.get("tags", {})
    top_tags = sorted(
        [{"tag": k, "count": v["count"], "url": v["url"]} for k, v in tags_raw.items()],
        key=lambda x: x["count"],
        reverse=True,
    )[:10]

    # search-index total (may differ from sum of change_counts due to multi-tag rows)
    try:
        si = load(ROOT / "search-index.json")
        total_entries = si.get("total", sum(totals.values()))
    except FileNotFoundError:
        total_entries = sum(totals.values())

    stats = {
        "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "latest_version": index["latest_version"],
        "last_polled_at": index.get("last_polled_at"),
        "total_patches": len(versions),
        "total_entries": total_entries,
        "change_totals": totals,
        "avg_days_between_patches": avg_cadence,
        "top_tags": top_tags,
        "patch_cadence": list(reversed(cadence)),  # newest-first for consumers
    }

    out = ROOT / "stats.json"
    with open(out, "w") as f:
        json.dump(stats, f, indent=2)
        f.write("\n")

    print(f"stats.json written — {len(versions)} patches, {total_entries} entries, avg cadence {avg_cadence}d")

if __name__ == "__main__":
    main()
