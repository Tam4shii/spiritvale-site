#!/usr/bin/env python3
"""SpiritVale MCP server — exposes patch data as Claude-native tools.

Works against local repo files (no live URL needed). Mirrors the same JSON
contract as spiritvale.tama.sh endpoints so Claude and other MCP clients can
query patch data without fetching HTTP.

Install:  pip install fastmcp
Run:      python mcp/server.py
"""
from __future__ import annotations

import json
from collections import defaultdict
from pathlib import Path

from fastmcp import FastMCP

REPO = Path(__file__).parent.parent
PATCHES = REPO / "patches"

mcp = FastMCP("spiritvale")


@mcp.tool()
def get_latest_patch() -> dict:
    """Return the latest SpiritVale patch note (version, title, changes)."""
    return json.loads((PATCHES / "latest.json").read_text())


@mcp.tool()
def list_patches() -> dict:
    """List all known patch versions with dates and change counts."""
    index = json.loads((PATCHES / "index.json").read_text())
    return {
        "latest_version": index.get("latest_version"),
        "total_versions": len(index.get("versions", [])),
        "versions": [
            {
                "version": v["version"],
                "title": v["title"],
                "date": v["date"],
                "change_counts": v.get("change_counts", {}),
            }
            for v in index.get("versions", [])
        ],
    }


@mcp.tool()
def get_patch(version: str) -> dict:
    """Return full patch data for a specific version string (e.g. '0.18.0').

    Use list_patches() first to see available versions.
    """
    path = PATCHES / f"v{version}.json"
    if not path.exists():
        raise ValueError(
            f"Patch v{version} not found. Call list_patches() to see available versions."
        )
    return json.loads(path.read_text())


@mcp.tool()
def search_patches(query: str) -> list[dict]:
    """Search all patch bullet points by keyword. Returns up to 20 matching entries."""
    index_path = REPO / "search-index.json"
    if not index_path.exists():
        return []
    index = json.loads(index_path.read_text())
    q = query.lower()
    return [
        {
            "version": e["version"],
            "type": e["type"],
            "text": e["text"],
            "url": e.get("url", f"/patch/?v={e['version']}"),
        }
        for e in index.get("entries", [])
        if q in e.get("text", "").lower()
    ][:20]


@mcp.tool()
def get_diff(version_from: str, version_to: str) -> dict:
    """Return cumulative changes between two patch versions (inclusive range).

    All added/changed/fixed/removed entries across the range are returned with
    per-entry version labels so you can see which patch introduced each change.
    """
    index = json.loads((PATCHES / "index.json").read_text())
    versions = [v["version"] for v in index.get("versions", [])]
    versions.reverse()  # oldest → newest
    try:
        i_from = versions.index(version_from)
        i_to = versions.index(version_to)
    except ValueError as exc:
        available = ", ".join(versions)
        raise ValueError(
            f"Version not found ({exc}). Available: {available}"
        ) from exc
    if i_from > i_to:
        i_from, i_to = i_to, i_from
    result: dict[str, list] = {"added": [], "changed": [], "fixed": [], "removed": []}
    for ver in versions[i_from : i_to + 1]:
        path = PATCHES / f"v{ver}.json"
        if not path.exists():
            continue
        patch = json.loads(path.read_text())
        for key in result:
            for entry in patch.get(key, []):
                text = entry if isinstance(entry, str) else entry.get("text", str(entry))
                result[key].append({"version": ver, "text": text})
    totals = {k: len(v) for k, v in result.items()}
    return {"from": version_from, "to": version_to, "totals": totals, **result}


@mcp.tool()
def get_tag_timeline(tag: str | None = None) -> dict:
    """Return per-version change counts for a tag — shows buff/nerf trend over patches.

    Pass a tag (e.g. 'shinobi', 'balance', 'necromancer') to see its history across
    all versions. Omit tag to get a summary of every tag. Use list_patches() for dates.

    Inspired by poe.ninja class-activity charts: turns raw bullet lists into trends.
    """
    index_path = REPO / "search-index.json"
    if not index_path.exists():
        return {}
    entries = json.loads(index_path.read_text()).get("entries", [])

    patches_index = json.loads((PATCHES / "index.json").read_text())
    version_dates = {v["version"]: v["date"] for v in patches_index.get("versions", [])}
    version_order = [v["version"] for v in reversed(patches_index.get("versions", []))]

    # {tag: {version: {type: count}}}
    data: dict = defaultdict(lambda: defaultdict(lambda: defaultdict(int)))
    for e in entries:
        ver = e["version"]
        etype = e.get("type", "changed")
        for t in e.get("tags", []):
            data[t][ver][etype] += 1

    def format_series(t: str) -> list[dict]:
        return [
            {
                "version": ver,
                "date": version_dates.get(ver, ""),
                "added": data[t][ver].get("added", 0),
                "changed": data[t][ver].get("changed", 0),
                "fixed": data[t][ver].get("fixed", 0),
                "removed": data[t][ver].get("removed", 0),
                "total": sum(data[t][ver].values()),
            }
            for ver in version_order
            if ver in data[t]
        ]

    if tag:
        if tag not in data:
            raise ValueError(
                f"Tag '{tag}' not found. Known tags: {sorted(data.keys())}"
            )
        return {"tag": tag, "timeline": format_series(tag)}

    return {"tags": {t: format_series(t) for t in sorted(data.keys())}}


if __name__ == "__main__":
    mcp.run()
