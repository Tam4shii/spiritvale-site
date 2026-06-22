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
import urllib.error
import urllib.request

_BASE = "https://spiritvale.tama.sh"


def _get(path: str) -> dict:
    url = f"{_BASE}{path}"
    with urllib.request.urlopen(url) as resp:
        return json.loads(resp.read().decode())


def _get_conditional(path, etag=None):
    """Conditional GET using If-None-Match. Returns (data, new_etag) or (None, etag) on 304."""
    url = f"{_BASE}{path}"
    req = urllib.request.Request(url)
    if etag:
        req.add_header("If-None-Match", etag)
    try:
        with urllib.request.urlopen(req) as resp:
            return json.loads(resp.read().decode()), resp.headers.get("ETag")
    except urllib.error.HTTPError as exc:
        if exc.code == 304:
            return None, etag
        raise


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


def get_entity_index() -> dict:
    """Entity index — all tracked entities with patch mention counts (/entity/index.json).

    Keys: generated_at (str), entities (dict of slug → {name, count, text_only_count, url}).
    Slugs: 'boss', 'shinobi', 'berserker', 'necromancer', 'echoing-spire', 'forgotten-depths', 'arena'.

    Example:
        idx = get_entity_index()
        for slug, e in idx['entities'].items():
            print(f"{e['name']}: {e['count']} patch mentions")
    """
    return _get("/entity/index.json")


def get_bot_json() -> dict:
    """Pre-formatted Discord embed payload (/patches/bot.json).

    Returns the bot.json envelope which includes a pre-built Discord embed dict under
    result['latest']['embed']. Consuming this avoids re-building embeds from raw patch
    data — the same pattern used by tarkov.dev's reference Stash Discord bot.

    Example:
        data = get_bot_json()
        embed_dict = data['latest']['embed']  # ready for discord.Embed.from_dict()
    """
    return _get("/patches/bot.json")


def get_latest_if_changed(etag=None):
    """Conditional GET for the latest patch — efficient for bots polling on a schedule.

    Returns (data, new_etag) when the patch changed; (None, same_etag) when unchanged (HTTP 304).
    Store the returned etag across calls so the CDN can skip the response body when nothing changed.

    Pattern from warframestat.us Discord bot fleet — avoids re-processing unchanged data on
    every poll tick, which matters when hundreds of bots poll the same endpoint every 5 minutes.

    Example (discord.py bot polling every 5 min):
        etag = None
        while True:
            patch, etag = get_latest_if_changed(etag)
            if patch:
                await channel.send(f"New patch: {patch['title']}")
            await asyncio.sleep(300)
    """
    return _get_conditional("/patches/latest.json", etag)
