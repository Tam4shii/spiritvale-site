#!/usr/bin/env python3
"""Generate api/health.json — structured freshness endpoint.

Derives stale/warn/critical booleans from stats.json so external monitors
(Grafana, uptime bots, Discord status commands) can consume health state
without doing timestamp math client-side.

Severity rules:
  ok       — polled within the last 24 hours
  warn     — 24–72 hours since last poll
  critical — >72 hours since last poll OR stats.json missing

Run: python3 scripts/build-health.py  OR  make health
"""
import json
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).parent.parent
STEAM_BASELINE_PATH = ROOT / "state" / "steam-last-count.txt"


def _read_steam_baseline() -> int | None:
    """Return the last-recorded Steam newsitems count, or None if not set."""
    try:
        return int(STEAM_BASELINE_PATH.read_text().strip())
    except (FileNotFoundError, ValueError):
        return None


def main():
    out_dir = ROOT / "api"
    out_dir.mkdir(exist_ok=True)

    try:
        with open(ROOT / "stats.json") as f:
            stats = json.load(f)
    except FileNotFoundError:
        health = {
            "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "stale": True,
            "hours_since_poll": None,
            "severity": "critical",
            "message": "stats.json not found — run make stats",
            "latest_version": None,
            "total_patches": None,
        }
        _write(out_dir / "health.json", health)
        return

    last_polled = stats.get("last_polled_at")
    hours_since = None
    if last_polled:
        polled_dt = datetime.fromisoformat(last_polled.replace("Z", "+00:00"))
        delta = datetime.now(timezone.utc) - polled_dt
        hours_since = round(delta.total_seconds() / 3600, 1)

    if hours_since is None:
        severity = "warn"
        stale = True
        message = "last_polled_at missing from stats.json"
    elif hours_since <= 24:
        severity = "ok"
        stale = False
        message = f"polled {hours_since}h ago"
    elif hours_since <= 72:
        severity = "warn"
        stale = True
        message = f"poll is {hours_since}h old (>24h threshold)"
    else:
        severity = "critical"
        stale = True
        message = f"poll is {hours_since}h old (>72h — Steam check may be broken)"

    steam_baseline = _read_steam_baseline()
    total_patches = stats.get("total_patches")

    # hours_since_poll semantics: 0.0 is the expected value immediately after a poll run.
    # Non-zero values reflect drift since the last Steam check — anything >24h triggers warn.
    health = {
        "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "stale": stale,
        "hours_since_poll": hours_since,
        "hours_since_poll_note": "0.0 = measured immediately after a poll; non-zero = drift since last Steam check",
        "severity": severity,
        "message": message,
        "latest_version": stats.get("latest_version"),
        "total_patches": total_patches,
        "steam_newsitems_baseline": steam_baseline,
        "steam_baseline_match": (total_patches == steam_baseline) if (total_patches is not None and steam_baseline is not None) else None,
    }
    _write(out_dir / "health.json", health)
    baseline_note = f", baseline={steam_baseline}, match={health['steam_baseline_match']}" if steam_baseline else ""
    print(f"api/health.json written — severity={severity}, hours_since_poll={hours_since}{baseline_note}")


def _write(path: Path, data: dict):
    with open(path, "w") as f:
        json.dump(data, f, indent=2)
        f.write("\n")


if __name__ == "__main__":
    main()
