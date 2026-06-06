#!/usr/bin/env python3
"""Generate shields.io Endpoint-URL badges for current patch version and freshness.

Badges:
  badge/latest.json    — current patch version (e.g. "v0.18.0")
  badge/freshness.json — days since last patch with staleness-aware color
                         (wago.tools "current build" freshness badge pattern)

Embed in README or Discord:
  https://img.shields.io/endpoint?url=https://spiritvale.tama.sh/badge/latest.json
  https://img.shields.io/endpoint?url=https://spiritvale.tama.sh/badge/freshness.json

Run: python3 scripts/build-badge.py  OR  make badge
"""
import json
from datetime import date
from pathlib import Path

ROOT = Path(__file__).parent.parent

# Staleness color thresholds (days since latest patch release).
# Mirrors wago.tools "current build" badge: green=fresh, yellow=aging, orange=stale, red=very stale.
_FRESHNESS_COLORS = [
    (7,  "brightgreen"),   # ≤7 days
    (14, "yellow"),        # 8–14 days
    (30, "orange"),        # 15–30 days
    (float("inf"), "red"), # >30 days
]


def _freshness_color(days: int) -> str:
    for threshold, color in _FRESHNESS_COLORS:
        if days <= threshold:
            return color
    return "red"


def _days_label(days: int) -> str:
    if days == 0:
        return "today"
    if days == 1:
        return "1 day ago"
    return f"{days} days ago"


def main():
    with open(ROOT / "patches" / "index.json") as f:
        index = json.load(f)

    version = index["latest_version"]
    out_dir = ROOT / "badge"
    out_dir.mkdir(exist_ok=True)

    # --- badge/latest.json: version badge ---
    latest_badge = {
        "schemaVersion": 1,
        "label": "SpiritVale",
        "message": f"v{version}",
        "color": "7c3aed",
    }
    _write(out_dir / "latest.json", latest_badge)
    print(f"badge/latest.json written — version={version}")

    # --- badge/freshness.json: staleness-aware badge ---
    latest_entry = next(
        (v for v in index.get("versions", []) if v.get("current")), None
    )
    if latest_entry and latest_entry.get("date"):
        patch_date = date.fromisoformat(latest_entry["date"])
        days_since = (date.today() - patch_date).days
        color = _freshness_color(days_since)
        message = _days_label(days_since)
    else:
        days_since = None
        color = "lightgrey"
        message = "unknown"

    freshness_badge = {
        "schemaVersion": 1,
        "label": "last patch",
        "message": message,
        "color": color,
    }
    _write(out_dir / "freshness.json", freshness_badge)
    print(f"badge/freshness.json written — days_since={days_since}, color={color}")


def _write(path: Path, data: dict):
    with open(path, "w") as f:
        json.dump(data, f, indent=2)
        f.write("\n")


if __name__ == "__main__":
    main()
