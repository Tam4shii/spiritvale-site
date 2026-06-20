#!/usr/bin/env python3
"""discord-example.py — SpiritVale patch watcher for Discord (Python, zero deps)

Polls patches/latest.json and posts a pre-built embed to a Discord webhook
whenever a new patch is detected.  Persists last-seen version to .last-version.

Usage:
    DISCORD_WEBHOOK=https://discord.com/api/webhooks/ID/TOKEN python3 discord-example.py

Optional env vars:
    POLL_INTERVAL   polling cadence in seconds (default: 600)
    STATE_FILE      path to version-state file (default: .last-version)

Requires: Python ≥ 3.8, no third-party packages.
Uses clients/spiritvale.py (two directories up) for API calls.
"""

import json
import os
import sys
import time
import urllib.request
from pathlib import Path

# Allow running from the bots/ directory or from the repo root.
sys.path.insert(0, str(Path(__file__).parent.parent / "clients"))
from spiritvale import get_bot_json  # pre-built embed, pattern: tarkov.dev/Stash

WEBHOOK = os.environ.get("DISCORD_WEBHOOK", "")
POLL_INTERVAL = int(os.environ.get("POLL_INTERVAL", "600"))
STATE_FILE = Path(os.environ.get("STATE_FILE", Path(__file__).parent / ".last-version"))

if not WEBHOOK:
    sys.exit("Missing DISCORD_WEBHOOK env var")


def load_seen_version() -> str | None:
    try:
        return STATE_FILE.read_text().strip() or None
    except FileNotFoundError:
        return None


def save_seen_version(version: str) -> None:
    STATE_FILE.write_text(version)


def post_embed(embed: dict) -> None:
    payload = json.dumps({"embeds": [embed]}).encode()
    req = urllib.request.Request(
        WEBHOOK, data=payload, headers={"Content-Type": "application/json"}, method="POST"
    )
    with urllib.request.urlopen(req, timeout=10) as resp:
        if resp.status not in (200, 204):
            print(f"[spiritvale-bot] webhook returned {resp.status}")


def poll() -> None:
    data = get_bot_json()
    latest = data["latest"]
    version = latest["version"]
    seen = load_seen_version()

    if seen is None:
        save_seen_version(version)
        print(f"[spiritvale-bot] watching from v{version}")
        return

    if version == seen:
        return

    embed = latest["embed"]
    post_embed(embed)
    save_seen_version(version)
    print(f"[spiritvale-bot] posted v{version} to Discord")


if __name__ == "__main__":
    print(f"[spiritvale-bot] starting — poll every {POLL_INTERVAL}s")
    while True:
        try:
            poll()
        except Exception as exc:
            print(f"[spiritvale-bot] poll error: {exc}")
        time.sleep(POLL_INTERVAL)
