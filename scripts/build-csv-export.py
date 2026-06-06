#!/usr/bin/env python3
"""Generate patches/export.csv — flat CSV of every patch entry.

wago.tools pattern: structured data export lets data scientists, Discord-bot
authors, and community tools consume the full patch history without parsing HTML
or running JS. CSV is universally importable (Excel, pandas, R, Google Sheets).

Columns: id, version, patch_title, date, type, text, tags, url
Source:  search-index.json (already flattened by build-search-index.py)
Output:  patches/export.csv

Run: python3 scripts/build-csv-export.py  OR  make csv
"""
import csv
import json
from pathlib import Path

ROOT = Path(__file__).parent.parent
INDEX_PATH = ROOT / "search-index.json"
OUT_PATH = ROOT / "patches" / "export.csv"

COLUMNS = ["id", "version", "patch_title", "date", "type", "text", "tags", "url"]


def main() -> None:
    with open(INDEX_PATH) as f:
        data = json.load(f)

    entries = data.get("entries", [])
    if not entries:
        print("search-index.json has no entries — run make index first")
        raise SystemExit(1)

    with open(OUT_PATH, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=COLUMNS, extrasaction="ignore")
        writer.writeheader()
        for entry in entries:
            row = dict(entry)
            # Flatten tags list → semicolon-delimited string for single-cell compat
            row["tags"] = ";".join(entry.get("tags", []))
            writer.writerow(row)

    print(f"patches/export.csv written — {len(entries)} entries")


if __name__ == "__main__":
    main()
