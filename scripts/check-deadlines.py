#!/usr/bin/env python3
"""Check state/persistent-blockers.json for time-sensitive deadlines.

Distinct from stale-draft alerts: this script fires ONLY on calendar deadlines,
not on seen_count thresholds. Separate escalation ladder prevents conflation.

Severity ladder:
  critical  — ≤2 days (exits non-zero; use in CI or make check-deadlines)
  urgent    — ≤5 days (exits non-zero)
  warn      — ≤14 days (exits 0 but prints loud header)
  ok        — >14 days or no deadline (silent pass)
  expired   — deadline already passed (exits non-zero)

Writes state/deadline-status.json with per-blocker results.

Run: python3 scripts/check-deadlines.py  OR  make check-deadlines
"""
import json
import sys
from datetime import date, datetime, timezone
from pathlib import Path

ROOT = Path(__file__).parent.parent
BLOCKERS_PATH = ROOT / "state" / "persistent-blockers.json"
STATUS_PATH = ROOT / "state" / "deadline-status.json"

SEVERITY_DAYS = {
    "expired": -1,
    "critical": 2,
    "urgent": 5,
    "warn": 14,
    "ok": float("inf"),
}


def classify(days_until: int) -> str:
    if days_until < 0:
        return "expired"
    if days_until <= SEVERITY_DAYS["critical"]:
        return "critical"
    if days_until <= SEVERITY_DAYS["urgent"]:
        return "urgent"
    if days_until <= SEVERITY_DAYS["warn"]:
        return "warn"
    return "ok"


def _editorial_risk(worst_severity: str) -> str:
    """Map deadline severity to a human editorial-risk label."""
    return {
        "expired": "high",
        "critical": "high",
        "urgent": "medium",
        "warn": "low",
        "ok": "low",
    }.get(worst_severity, "unknown")


def _check_idempotency(blockers: dict, worst: str, today) -> bool:
    """Return True if the worst-severity blocker was already alerted at this level today."""
    for blocker in blockers.values():
        if blocker.get("last_severity") != worst:
            continue
        last_alerted = blocker.get("last_alerted_at", "")
        if last_alerted.startswith(str(today)):
            return True
    return False


def main():
    if not BLOCKERS_PATH.exists():
        print("state/persistent-blockers.json not found — no deadline tracking active")
        sys.exit(0)

    with open(BLOCKERS_PATH) as f:
        blockers = json.load(f)

    today = date.today()
    results = []
    worst = "ok"
    severity_rank = ["ok", "warn", "urgent", "critical", "expired"]

    for key, blocker in blockers.items():
        deadline_str = blocker.get("deadline")
        if not deadline_str:
            continue

        deadline = date.fromisoformat(deadline_str)
        days_until = (deadline - today).days
        severity = classify(days_until)

        entry = {
            "key": key,
            "description": blocker.get("description", key),
            "deadline": deadline_str,
            "days_until": days_until,
            "severity": severity,
        }
        results.append(entry)

        if severity_rank.index(severity) > severity_rank.index(worst):
            worst = severity

        _print_entry(entry)

    # Operational risk is always LOW for this script — it is read-only and makes no
    # content changes. Editorial risk is derived from deadline severity.
    editorial_risk = _editorial_risk(worst)

    # Idempotency advisory: read last_severity from persistent-blockers to detect
    # whether the worst-severity blocker has already been alerted at this level today.
    already_alerted = _check_idempotency(blockers, worst, today)

    status = {
        "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "today": str(today),
        "worst_severity": worst,
        "operational_risk": "low",
        "editorial_risk": editorial_risk,
        "idempotency": {
            "already_alerted_today": already_alerted,
            "note": "alert skipped (same severity already logged today)" if already_alerted else "alert may fire",
        },
        "deadlines": results,
    }
    with open(STATUS_PATH, "w") as f:
        json.dump(status, f, indent=2)
        f.write("\n")

    print(f"\nstate/deadline-status.json written — worst_severity={worst}")
    print(f"\n── Risk Assessment ──")
    print(f"Operational risk : LOW  (read-only — no content or schema changes)")
    print(f"Editorial risk   : {editorial_risk.upper()}")
    if already_alerted:
        print(f"Idempotency      : already alerted at severity={worst} today — no repeat notification needed")
    else:
        print(f"Idempotency      : first alert at severity={worst} — notification may fire")

    if worst in ("critical", "urgent", "expired"):
        print(
            f"\n🚨 EXIT NON-ZERO: editorial risk={editorial_risk.upper()} (deadline severity={worst}) — boss action required",
            file=sys.stderr,
        )
        sys.exit(1)


def _print_entry(entry: dict):
    sev = entry["severity"]
    days = entry["days_until"]
    key = entry["key"]
    desc = entry["description"]
    deadline = entry["deadline"]

    icons = {"expired": "💀", "critical": "🚨", "urgent": "⚠️ ", "warn": "🟡", "ok": "✅"}
    icon = icons.get(sev, "❓")

    if sev == "expired":
        label = f"EXPIRED {abs(days)}d ago ({deadline})"
    elif sev in ("critical", "urgent"):
        label = f"{sev.upper()} — {days}d remaining (deadline {deadline})"
    elif sev == "warn":
        label = f"WARN — {days}d remaining (deadline {deadline})"
    else:
        label = f"OK — {days}d until deadline ({deadline})"

    print(f"{icon} [{key}] {label}")
    print(f"   {desc}")


if __name__ == "__main__":
    main()
