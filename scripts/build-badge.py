#!/usr/bin/env python3
"""Generate badge/latest.json — shields.io Endpoint-URL badge for the current patch version.

Embed in any README or Discord message:
  https://img.shields.io/endpoint?url=https://spiritvale.tama.sh/badge/latest.json

Run: python3 scripts/build-badge.py  OR  make badge
"""
import json
from pathlib import Path

ROOT = Path(__file__).parent.parent


def main():
    with open(ROOT / "patches" / "index.json") as f:
        index = json.load(f)

    version = index["latest_version"]
    badge = {
        "schemaVersion": 1,
        "label": "SpiritVale",
        "message": f"v{version}",
        "color": "7c3aed",
    }

    out_dir = ROOT / "badge"
    out_dir.mkdir(exist_ok=True)
    out_path = out_dir / "latest.json"
    with open(out_path, "w") as f:
        json.dump(badge, f, indent=2)
        f.write("\n")

    print(f"badge/latest.json written — version={version}")


if __name__ == "__main__":
    main()
