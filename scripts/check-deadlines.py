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
import os
import subprocess
import sys
from datetime import date, datetime, timezone
from pathlib import Path

ROOT = Path(__file__).parent.parent
BLOCKERS_PATH = ROOT / "state" / "persistent-blockers.json"
STATUS_PATH = ROOT / "state" / "deadline-status.json"

# Known quiet windows — no patches expected; alerts cap at "warn" (no Telegram, no exit 1).
# Pattern: warframestat.us / wago.tools document known quiet periods to prevent alert fatigue.
DEAD_WINDOWS: list[tuple[str, str]] = [
    ("2026-06-22", "2026-07-15"),  # EA polish window; Demo live, EA launches Jul 15
]

SEVERITY_DAYS = {
    "expired": -1,
    "critical": 2,
    "urgent": 5,
    "warn": 14,
    "ok": float("inf"),
}


def _in_dead_window(today: date) -> tuple[bool, str]:
    """Return (True, label) if today falls in any known quiet window."""
    for start_s, end_s in DEAD_WINDOWS:
        s, e = date.fromisoformat(start_s), date.fromisoformat(end_s)
        if s <= today <= e:
            return True, f"dead window {start_s}→{end_s}"
    return False, ""


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


LUNA_TG = os.environ.get("LUNA_TG", os.path.expanduser("~/.local/bin/luna-tg"))
ALERT_SEVERITIES = {"critical", "urgent", "expired"}


def _dead_window_active(blockers: dict, today) -> tuple[bool, str]:
    """Return (is_active, reason) if any blocker has a dead_window_until in the future."""
    for blocker in blockers.values():
        dw = blocker.get("dead_window_until")
        if not dw:
            continue
        try:
            dw_date = date.fromisoformat(dw)
        except ValueError:
            continue
        if today <= dw_date:
            reason = blocker.get("dead_window_reason", f"dead window until {dw}")
            return True, f"until {dw}: {reason}"
    return False, ""


def _send_tg_alert(worst: str, results: list, blockers: dict, today) -> bool:
    """Fire luna-tg when severity is critical/urgent/expired. Returns True if sent."""
    # Suppress alerts during declared dead window to prevent alert fatigue.
    dw_active, dw_reason = _dead_window_active(blockers, today)
    if dw_active:
        print(f"Dead window active — Telegram suppressed ({dw_reason})")
        return False

    if not os.path.isfile(LUNA_TG) or not os.access(LUNA_TG, os.X_OK):
        print(f"WARN: luna-tg not executable at {LUNA_TG} — Telegram alert skipped")
        return False
    lines = []
    for r in results:
        if r["severity"] in ALERT_SEVERITIES:
            d = r["days_until"]
            label = f"TOMORROW ({r['deadline']})" if d == 1 else (
                f"TODAY ({r['deadline']})" if d == 0 else
                f"EXPIRED {abs(d)}d ({r['deadline']})" if d < 0 else
                f"{d}d left ({r['deadline']})"
            )
            lines.append(f"🚨 [{r['key']}] {label}\n   {r['description']}")
    if not lines:
        return False
    msg = f"<b>SpiritVale Deadline Alert — {worst.upper()}</b>\n\n" + "\n\n".join(lines)
    try:
        subprocess.run([LUNA_TG, msg], timeout=10, check=True)
        print(f"Telegram alert sent (severity={worst})")
        return True
    except Exception as e:
        print(f"WARN: Telegram alert failed — {e}")
        return False


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
    dead_window, dead_window_label = _in_dead_window(today)
    if dead_window:
        print(f"[dead-window] {dead_window_label} — alert severity capped at warn; Telegram suppressed")

    results = []
    worst = "ok"
    severity_rank = ["ok", "warn", "urgent", "critical", "expired"]

    for key, blocker in blockers.items():
        if blocker.get("archived"):
            print(f"[archived] {key} — skipping (archived_at={blocker.get('archived_at', '?')})")
            continue
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

    # Dead-window cap: during known quiet periods, suppress actionable escalations.
    # Worst severity is capped at "warn" so Telegram doesn't fire and exit code stays 0.
    if dead_window and severity_rank.index(worst) > severity_rank.index("warn"):
        print(f"[dead-window] {dead_window_label} — downgrading worst={worst} to warn (no Telegram, no exit 1)")
        worst = "warn"

    # Operational risk is always LOW for this script — it is read-only and makes no
    # content changes. Editorial risk is derived from deadline severity.
    editorial_risk = _editorial_risk(worst)

    # Idempotency advisory: read last_severity from persistent-blockers to detect
    # whether the worst-severity blocker has already been alerted at this level today.
    already_alerted = _check_idempotency(blockers, worst, today)
    dw_active, dw_reason = _dead_window_active(blockers, today)

    status = {
        "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "today": str(today),
        "worst_severity": worst,
        "operational_risk": "low",
        "editorial_risk": editorial_risk,
        "dead_window": {
            "active": dw_active,
            "reason": dw_reason if dw_active else None,
        },
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
    if dw_active:
        print(f"Dead window      : ACTIVE ({dw_reason})")
    print(f"\n── Risk Assessment ──")
    print(f"Operational risk : LOW  (read-only — no content or schema changes)")
    print(f"Editorial risk   : {editorial_risk.upper()}")
    if worst in ALERT_SEVERITIES:
        if already_alerted:
            print(f"Idempotency      : already alerted at severity={worst} today — Telegram skipped")
        elif dw_active:
            print(f"Dead window      : alert suppressed until {dw_reason.split(':')[0]}")
        else:
            print(f"Idempotency      : first alert at severity={worst} — firing Telegram notification")
            _send_tg_alert(worst, results, blockers, today)
    else:
        print(f"Idempotency      : severity={worst} below alert threshold — no notification")

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
