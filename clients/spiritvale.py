"""
spiritvale.py — zero-dependency Python client for the SpiritVale Community Hub API

Usage:
    from spiritvale import get_latest, get_index, get_patch, get_search_index, get_diff

All functions are synchronous and return plain dicts/lists parsed from JSON.
Raises urllib.error.HTTPError on non-2xx responses.
CORS is open on the origin — no proxy needed for browser contexts.

Requires: Python ≥ 3.8 (no third-party dependencies)
"""

import json
import urllib.request

_BASE = "https://spiritvale.tama.sh"


def _get(path: str) -> dict:
    url = f"{_BASE}{path}"
    with urllib.request.urlopen(url) as resp:
        return json.loads(resp.read().decode())


def get_latest() -> dict:
    """Latest patch note (/patches/latest.json)."""
    return _get("/patches/latest.json")


def get_index() -> dict:
    """Full patch index — version list + poll metadata (/patches/index.json)."""
    return _get("/patches/index.json")


def get_patch(version: str) -> dict:
    """Single patch by version string, e.g. get_patch('0.17.0')."""
    return _get(f"/patches/v{version}.json")


def get_search_index() -> dict:
    """All classified bullet entries across every patch (/search-index.json)."""
    return _get("/search-index.json")


def get_health() -> dict:
    """Structured poll-freshness data (/api/health.json).

    Keys: severity ('ok'/'warn'/'critical'), stale (bool), hours_since_poll (float|None),
          message (str), latest_version (str|None), total_patches (int|None).
    """
    return _get("/api/health.json")


def get_diff(from_version: str, to_version: str) -> dict:
    """
    Cumulative diff between two versions (inclusive of to_version, exclusive of from_version).

    Returns a dict with keys: added, changed, fixed, removed, deprecated, security.
    Each value is a list of dicts with keys: text (str), _version (str).

    Example:
        diff = get_diff('0.13.0', '0.17.0')
        print(f"{len(diff['added'])} added, {len(diff['changed'])} changed")
    """
    index = get_index()
    versions = [v["version"] for v in index["versions"]]
    try:
        from_idx = versions.index(from_version)
        to_idx = versions.index(to_version)
    except ValueError as exc:
        raise ValueError(f"spiritvale: unknown version in get_diff — {exc}") from exc

    # index.versions is newest-first; slice from to_idx to from_idx, then reverse for chronological
    change_keys = ["added", "changed", "fixed", "removed", "deprecated", "security"]
    result: dict = {k: [] for k in change_keys}

    for v in reversed(versions[to_idx:from_idx]):
        patch = get_patch(v)
        for key in change_keys:
            for entry in patch.get(key) or []:
                result[key].append({"text": entry, "_version": v})

    return result
