#!/usr/bin/env python3
"""Generate server-side diff JSON endpoints.

Produces diff/v{from}...v{to}.json for every adjacent pair and every
cumulative span from oldest to each later version. These are immutable,
CDN-cacheable endpoints that bots and SDKs can fetch with a single request
instead of computing diffs client-side from N patch files.

URL pattern mirrors wago.tools (?from=X&to=Y) adapted for static hosting:
  /diff/v0.17.0...v0.18.0.json   — single-step diff
  /diff/v0.13.0...v0.18.0.json   — cumulative diff (all patches between)

Also writes diff/index.json listing all available diff endpoints.

Run: python3 scripts/build-diff-endpoints.py  OR  make diff-endpoints
"""
import json
from pathlib import Path

ROOT = Path(__file__).parent.parent
PATCHES_DIR = ROOT / "patches"
DIFF_DIR = ROOT / "diff"
INDEX_PATH = PATCHES_DIR / "index.json"

CHANGE_KEYS = ("added", "changed", "fixed", "removed")


def load_versions() -> list[str]:
    """Return versions in chronological order (oldest first)."""
    index = json.loads(INDEX_PATH.read_text())
    versions = [v["version"] for v in index["versions"]]
    return list(reversed(versions))  # index is newest-first


def load_patch(version: str) -> dict:
    path = PATCHES_DIR / f"v{version}.json"
    if not path.exists():
        return {}
    return json.loads(path.read_text())


def build_diff(from_version: str, to_version: str, versions: list[str]) -> dict:
    """Aggregate all changes from patches after from_version up to and including to_version."""
    from_idx = versions.index(from_version)
    to_idx = versions.index(to_version)
    span = versions[from_idx + 1 : to_idx + 1]

    result: dict[str, list] = {k: [] for k in CHANGE_KEYS}
    patch_metas = []

    for ver in span:
        patch = load_patch(ver)
        if not patch:
            continue
        for key in CHANGE_KEYS:
            result[key].extend(patch.get(key, []))
        patch_metas.append({
            "version": ver,
            "title": patch.get("title"),
            "date": patch.get("date"),
        })

    counts = {k: len(result[k]) for k in CHANGE_KEYS}
    return {
        "from": from_version,
        "to": to_version,
        "patches_included": [m["version"] for m in patch_metas],
        "patch_count": len(patch_metas),
        "patch_metas": patch_metas,
        **result,
        "change_counts": counts,
    }


def slug(from_v: str, to_v: str) -> str:
    return f"v{from_v}...v{to_v}.json"


def main():
    DIFF_DIR.mkdir(exist_ok=True)

    versions = load_versions()
    if len(versions) < 2:
        print("Not enough versions to diff — need at least 2.")
        return

    written = []

    # Adjacent pairs: v[i] → v[i+1]
    for i in range(len(versions) - 1):
        fv, tv = versions[i], versions[i + 1]
        diff = build_diff(fv, tv, versions)
        out = DIFF_DIR / slug(fv, tv)
        out.write_text(json.dumps(diff, indent=2) + "\n")
        written.append({"from": fv, "to": tv, "file": str(out.relative_to(ROOT))})

    # Cumulative spans: oldest → every later version
    oldest = versions[0]
    for tv in versions[2:]:  # skip adjacent (already written as v[0]→v[1])
        diff = build_diff(oldest, tv, versions)
        out = DIFF_DIR / slug(oldest, tv)
        out.write_text(json.dumps(diff, indent=2) + "\n")
        written.append({"from": oldest, "to": tv, "file": str(out.relative_to(ROOT))})

    # diff/index.json — registry of all generated endpoints
    index = {
        "endpoints": [
            {
                "from": e["from"],
                "to": e["to"],
                "url": f"/diff/v{e['from']}...v{e['to']}.json",
            }
            for e in written
        ],
        "total": len(written),
    }
    (DIFF_DIR / "index.json").write_text(json.dumps(index, indent=2) + "\n")

    print(f"diff/: wrote {len(written)} diff endpoints + index.json")
    for e in written:
        print(f"  {e['file']}")


if __name__ == "__main__":
    main()
